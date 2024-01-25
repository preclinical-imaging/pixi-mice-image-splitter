"""

"""
import logging
from io import BytesIO

import ipywidgets as ipw
import nibabel
import numpy as np
import skimage
import os
from PIL import Image, ImageDraw
from skimage import measure, filters
from skimage.measure import label
from skimage.morphology import disk
from skimage.morphology import (erosion, dilation)

from image_classes import PETImage, CTImage, DicomImage, SubImage
from rectangle import Rect

#  logging
logger = logging.getLogger(__name__)


# functions
def multi_dilation(im, num, footprint):
    for i in range(num):
        im = dilation(im, footprint)
    return im


def multi_erosion(im, num, footprint):
    for i in range(num):
        im = erosion(im, footprint)
    return im


# classes
class SoM:
    """
    Splitter of Mice class
    """

    margin = 30
    ipw_on = False

    def __init__(self, file, modality=None, dicom=False):
        self.blob_labels = None
        self.cuts = None
        self.filename = file
        self.pi, self.modality = SoM.load_image(file, modality, dicom)

    @staticmethod
    def add_cuts_to_image(im, boxes, desc_map, save_analyze_dir=None, dicom_metadata=None):

        ims = []

        mag = 2 if isinstance(im, PETImage) else 0.5
        for b in boxes:
            r, desc = b['rect'], desc_map[b['desc']]
            ix = len(im.cuts) + 1
            xmax, xmin = int(round(r.xrb)), int(round(r.xlt))
            ymax, ymin = int(round(r.yrb)), int(round(r.ylt))

            # If xmax is less than xmin, swap them
            if xmax < xmin:
                xmax, xmin = xmin, xmax

            # If ymax is less than ymin, swap them
            if ymax < ymin:
                ymax, ymin = ymin, ymax

            # print('xmax={},xmin={},ymax={},ymin={}'.format(xmax,xmin,ymax,ymin))
            fname = im.filename[:-4] + '_' + desc
            data = im.img_data[:, xmin:xmax, ymin:ymax, :]
            d, h, w = data.shape[0], data.shape[1], data.shape[2]

            if data.shape[3] == 1:
                ims += [SoM.a2im(im, np.squeeze(data[:, :, int(round(w * .5)), 0]), mag, False)]
            else:
                t2 = int(data.shape[3] / 2)
                ims += [SoM.a2im(im, np.squeeze(data[:, :, int(round(w * .5)), t2]), mag, False)]

            # _,data=im.submemmap(ix=ix,data=im.img_data[:,ymin:ymax,xmin:xmax,:])
            # print(data.shape)

            metadata = dicom_metadata[desc] if desc in dicom_metadata else None
            new_img = SubImage(parent_image=im, img_data=data, filename=fname + '.img',
                               cut_coords=[(xmin, xmax), (ymin, ymax)], desc=desc, metadata=metadata)

            # print('adding '+fname+'.img')
            # print('saving '+fname)
            if save_analyze_dir is not None:
                SoM.write_analyze(new_img, save_analyze_dir + '/' + fname + '_analyze.img')
            im.cuts.append(new_img)
        if SoM.ipw_on:
            print('split images(midsagittal slice)')
            box = ipw.HBox(ims)
            # display(box)
        return ims

    @staticmethod
    def write_analyze(im, filepath):
        id1 = np.swapaxes(im.img_data, 0, 2)
        ps = im.params.pixel_size
        hdr = nibabel.AnalyzeHeader()
        hdr.set_data_shape(id1.shape)
        hdr.set_data_dtype(id1.dtype)
        hdr.set_zooms([ps, ps, ps, im.params.frame_duration[0]])
        analyze_img = nibabel.AnalyzeImage(id1, None, hdr)
        print('writing Analyze 7.5 image: ' + filepath)
        analyze_img.to_filename(filepath)

    @staticmethod
    def a2im(pi, a, r, return_array=False):
        if isinstance(pi, PETImage):
            return SoM.a2im_pet(a, r, return_array)
        elif isinstance(pi, CTImage):
            return SoM.a2im_ct(a, r, return_array)
        else:
            return None

    @staticmethod
    def z_compress_pet(pi):
        n = 12
        img = pi.img_data
        if len(img.shape) == 3:
            imgz = np.squeeze(np.sum(img, axis=0))
        elif len(img.shape) == 4:
            imgz = np.squeeze(np.sum(img, axis=(0, 3)))
        else:
            logger.error(f"Unknown image shape: {img.shape}")
            raise (ValueError("Unknown image shape"))
        im = filters.gaussian(imgz, sigma=1 / (4. * n))
        return im

    @staticmethod
    def merge_im_arrays(im0, im1, orientation='horizontal', bg=0):
        a = im0
        ash = np.array(a.shape)
        b = im1
        bsh = np.array(b.shape)
        msh = np.maximum(np.array(a.shape), np.array(b.shape))
        da = msh - a.shape
        db = msh - b.shape
        if orientation == 'horizontal':
            ap = np.pad(a, [(0, da[0]), (0, 0)], constant_values=bg)
            bp = np.pad(b, [(0, db[0]), (0, 0)], constant_values=bg)
            # print(ap.shape,bp.shape)
            # print(a.dtype,b.dtype)
            im = np.concatenate((ap, bp), 1)
        else:
            ap = np.pad(a, [(0, da[1]), (0, 0)], constant_values=bg)
            bp = np.pad(b, [(0, db[1]), (0, 0)], constant_values=bg)
            # print(ap.shape,bp.shape)
            im = np.concatenate((ap, bp), 0)
        return im

    def split_mice(self, outdir, save_analyze=False, num_anim=None,
                   sep_thresh=None, margin=None, minpix=None, output_qc=False,
                   suffix_map=None, zip=False, remove_bed=False, dicom_metadata=None,
                   pet_img_size=None, ct_img_size=None):

        d = {'l': 'l', 'r': 'r', 'ctr': 'ctr', 'lb': 'lb', 'rb': 'rb', 'lt': 'lt', 'rt': 'rt'}
        if suffix_map is not None:
            for s in suffix_map.split(','):
                mp = s.split(':')
                if len(mp) < 2: continue
                if mp[0] in d.keys(): d[mp[0]] = mp[1]

        if self.modality == 'PET' or self.modality == 'PT':
            margin = 4 if margin is None else margin
            minpix = 200 if minpix is None else minpix
            return self.split_mice_pet(outdir, d, save_analyze, num_anim, sep_thresh, margin, minpix,
                                       output_qc, zip, dicom_metadata, pet_img_size)
        if self.modality == 'CT':
            margin = 20 if margin is None else margin
            minpix = 3300 if minpix is None else minpix
            return self.split_mice_ct(outdir, d, save_analyze, num_anim, sep_thresh,
                                      margin, minpix, output_qc, remove_bed, zip, dicom_metadata, ct_img_size)
        else:
            logger.error(f"Unknown modality: {self.modality}. Cannot split mice.")
            return -1

    @staticmethod
    def detect_animals(im):
        blobs = im > SoM.sep_thresh * np.mean(im)
        # all_labels = measure.label(blobs)
        (blobs_labels, num) = measure.label(blobs, return_num=True, background=0)
        return blobs_labels, num

    @staticmethod
    def get_valid_regs(label):
        min_pts = SoM.minpix
        m = [SoM.margin, SoM.margin]
        props = measure.regionprops(label)
        areas = [p.area for p in props]
        logger.info('areas' + str(areas))
        logger.debug('centers' + str([p.centroid for p in props]))
        logger.debug('bboxes' + str([p.bbox for p in props]))
        valid_reg = [p for p in props if p.area >= min_pts]
        logger.info('valid regions detected: ' + str(len(valid_reg)))
        return valid_reg

    @staticmethod
    def harmonize_rects(rects):
        num_rect = len(rects)
        if num_rect == 1:
            r = rects['ctr']
            sz = int(round(max(r.wid(), r.ht())))
            r.adjust_to_size([sz, sz])
        elif num_rect == 2:
            rl, rr = rects['l'], rects['r']
            max_hw = max(rl.wid(), rr.wid(), rl.ht(), rr.ht())
            rl.adjust_to_size([max_hw, max_hw])
            rr.adjust_to_size([max_hw, max_hw])
        elif num_rect == 3 or num_rect == 4:
            rs = [l['rect'] for l in rects]
            sz = int(round(max([max(r.wid(), r.ht()) for r in rs])))
            s = [sz, sz]
            for r in rs:
                r.adjust_to_size(s)

    @staticmethod
    def split_coords(img, valid_reg):
        ims = []
        out_boxes = []
        m = [SoM.margin, SoM.margin]
        logger.info('split images (axial projection):')
        if len(valid_reg) == 1:
            bb = valid_reg[0].bbox
            r = Rect(bb=bb)
            r.expand(m)
            SoM.harmonize_rects({'ctr': r})
            out_boxes += [{'desc': 'ctr', 'rect': r}]

        elif len(valid_reg) == 2:
            bb1, bb2 = valid_reg[0].bbox, valid_reg[1].bbox

            if bb1[1] < bb2[1]:
                rl = Rect(bb=bb1)
                rr = Rect(bb=bb2)
            else:
                rl = Rect(bb=bb2)
                rr = Rect(bb=bb1)
            rl.expand(m)
            rr.expand(m)

            # if the rect has expanded beyond the image, adjust it to the image size
            if rl.xlt < 0:
                rl.xlt = 0
            if rl.ylt < 0:
                rl.ylt = 0
            if rr.xrb > img.shape[1]:
                rr.xrb = img.shape[1]
            if rr.yrb > img.shape[0]:
                rr.yrb = img.shape[0]

            SoM.harmonize_rects({'l': rl, 'r': rr})
            out_boxes += [{'desc': 'l', 'rect': rl}, {'desc': 'r', 'rect': rr}]

        elif len(valid_reg) == 3 or len(valid_reg) == 4:
            rs = [Rect(bb=valid_reg[i].bbox) for i in range(len(valid_reg))]
            big_box = Rect.union_list(rs)
            lr = [{'desc': big_box.quadrant(r.ctr()), 'rect': r} for r in rs]
            SoM.harmonize_rects(lr)
            out_boxes = lr
        return out_boxes

    @staticmethod
    def refine_cuts_ct(cuts, imz):
        sz = imz.shape
        for box in cuts:
            r = box['rect']
            cx, cy, n = 0., 0., 0.
            for y in range(max(0, r.ylt), min(r.yrb, sz[0])):
                for x in range(max(0, r.xlt), min(r.xrb, sz[1])):
                    if imz[y, x] == 0: continue
                    cx += x
                    cy += y
                    n += 1
            r.adjust_to_center(cx / n, cy / n)
        return cuts

    @staticmethod
    def z_compress_ct(pi, thresh, binary=True):
        img = pi.img_data
        sh = img.shape
        nsl = sh[0]

        if not binary:
            return np.squeeze(img[int(nsl / 2), :, :])

        sl = np.zeros((sh[1], sh[2])).astype('float32')
        for z in range(nsl):
            slm = np.squeeze(img[z, :, :])
            if binary:
                slm = np.where(slm > thresh, 1, 0)
            sl += slm

        sl /= float(nsl)
        return sl / float(nsl)

    def detect_animals_ct(im, thresh):
        logger.info(f"Detecting animals with threshold: {thresh}")
        blobs = im > thresh
        (blobs_labels, num) = measure.label(blobs, return_num=True, background=0)
        return blobs_labels, num

    @staticmethod
    def a2im_pet(a, r, return_array=False):
        if not SoM.ipw_on and not return_array: return None
        f = BytesIO()
        b = 0.3
        im0 = (a / (np.max(a) * b))
        im0[im0 > 1] = 1
        arr = np.uint8(im0 * 255)
        if return_array: return arr
        if not SoM.ipw_on: return None
        img = Image.fromarray(arr)
        img.save(f, 'png')
        layout = {'width': str(r * a.shape[1]) + 'px', 'height': str(r * a.shape[0]) + 'px'}
        # print(layout)
        return ipw.Image(value=f.getvalue(), layout=layout)

    @staticmethod
    def a2im_ct(a, r, return_array=False):
        im0 = np.float64(a)
        im0[im0 < 0] = 0
        im0[im0 > 200.] = 200.
        arr = np.uint8((im0 / np.max(im0)) * 255.)

        if return_array: return arr
        if not SoM.ipw_on: return None

        f = BytesIO()
        img = Image.fromarray(arr)
        img.save(f, 'png')
        layout = {'width': str(r * a.shape[1]) + 'px', 'height': str(r * a.shape[0]) + 'px'}
        return ipw.Image(value=f.getvalue(), layout=layout)

    @staticmethod
    def get_sag_image(img_data):
        # print('get_sag_image shape:',img_data.shape)
        sh = img_data.shape
        if len(sh) < 4:
            return np.squeeze(img_data[:, np.int32(sh[1] / 2), :])
        else:
            return np.squeeze(img_data[:, np.int32(sh[1] / 2), :, np.int32(sh[3] / 2)])

    @staticmethod
    def combine_images(images, mode='horizontal'):
        widths, heights = zip(*(i.size for i in images))
        if mode == 'horizontal':
            total_width, max_height = sum(widths), max(heights)
            new_im = Image.new('RGB', (total_width, max_height))
            x_offset = 0
            for im in images:
                new_im.paste(im, (x_offset, 0))
                x_offset += im.size[0]
            return new_im
        else:
            total_height = sum(heights)
            max_width = max(widths)
            new_im = Image.new('RGB', (max_width, total_height))
            y_offset = 0
            for im in images:
                new_im.paste(im, (0, y_offset))
                y_offset += im.size[1]
            return new_im

    @staticmethod
    def display_pil_image(im):
        if SoM.ipw_on:
            f = BytesIO()
            im.save(f, 'png')
            # display(ipw.HBox([ipw.Image(value=f.getvalue())]))

    @staticmethod
    def load_image_ex(file, modality):
        pi = None
        if modality == 'PET':
            try:
                pi = PETImage(file)
                pi.load_header()
                pi.load_image()
            except Exception as e:
                print(str(e))
                return None, None
            return pi, modality
        elif modality == 'CT':
            try:
                pi = CTImage(file)
                pi.load_header()
                pi.load_image()
            except Exception as e:
                print(str(e))
                return None, None
            return pi, modality
        else:
            print('error: unknown modality')
            return None, None

    @staticmethod
    def load_image(file, modality=None, dicom=False, **kwargs):
        if dicom:
            try:
                pi = DicomImage(file)
                pi.load_image()
                return pi, pi.modality
            except Exception as e:
                logger.error(f"Failed to load dicom image: {file}. Error: {e}")
                return None, None

        if modality is not None:
            return SoM.load_image_ex(file, modality.upper())

        detect_mod = None
        try:
            print('checking if PET modality')
            pi = PETImage(file)
            pi.load_header()
            detect_mod = 'PET'
        except Exception as e:
            print(str(e))
            pi = None

        if pi == None:
            try:
                print('checking if CT modality')
                pi = CTImage(file)
                pi.load_header()
                detect_mod = 'CT'
            except Exception as e:
                print(str(e))
                pi = None

        if pi is None:
            print('Could not load image as PET or CT modality')
            return None, None

        if modality is not None and detect_mod != modality:
            print(modality, ' modality expected, but ', detect_mod, 'detected, exiting')
            return None, None
        print(detect_mod, ' modality detected')
        pi.load_image()
        return pi, detect_mod

    @staticmethod
    def remove_bed(img):
        logger.info('Removing bed')
        footprint = disk(10)
        eroded = multi_erosion(img, 2, footprint)
        dilated = multi_dilation(eroded, 2, footprint)
        return dilated

    @staticmethod
    def write_images(pi, outdir, zip=False):
        for ind in range(len(pi.cuts)):
            pi.save_cut(ind, f"{outdir}/", zip=zip)

    def split_mice_ct(self, outdir, desc_map, save_analyze=False, num_anim=None,
                      sep_thresh=0.99, margin=20, minpix=3300, output_qc=False,
                      bed_removal=True, zip=False, dicom_metadata=None, img_size=None):
        logger.info('Splitting CT image ' + self.pi.filename)

        SoM.num_anim = num_anim
        SoM.sep_thresh = sep_thresh
        SoM.margin = margin
        SoM.minpix = minpix

        logger.debug(f"num_anim={num_anim}, sep_thresh={sep_thresh}, margin={margin}, minpix={minpix}")

        pi = self.pi
        imz = SoM.z_compress_ct(pi, 50, False)

        # Automatic thresholding for dicom images
        thresh = None

        if self.pi.image_format == 'dicom':
            thresh = filters.threshold_li(imz)
            logger.info(f"Automatic thresholding for dicom images: {thresh}")
        else:
            thresh = 0.1
            logger.info(f"Manual thresholding for microPET images: {thresh}")

        if bed_removal:
            imz = SoM.remove_bed(imz)

        blobs_labels, num = SoM.detect_animals_ct(imz, thresh)
        rects = SoM.get_valid_regs(blobs_labels)
        cuts = SoM.split_coords(imz, rects)

        # adjust the size of the cuts if img_size is specified.
        # helpful for keeping the same image size across multiple scans.
        if img_size is not None:
            for cut in cuts:
                cut['rect'].adjust_to_size(img_size)

        save_analyze_dir = outdir if save_analyze else None
        # save_analyze_dir=None #debug
        SoM.add_cuts_to_image(pi, cuts, desc_map, save_analyze_dir, dicom_metadata)

        # write the images.
        if outdir is not None:
            SoM.write_images(pi, outdir, zip=zip)

        if output_qc:
            im = SoM.qc_image(pi, blobs_labels, cuts, outdir, desc_map)
            SoM.display_pil_image(im)

        # pi.clean_cuts()
        # pi.unload_image()
        return 0

    def split_mice_pet(self, outdir, desc_map, save_analyze=False, num_anim=None,
                       sep_thresh=None, margin=20, minpix=200, output_qc=False,
                       zip=False, dicom_metadata=None, img_size=None):
        logger.info('Splitting PET image ' + self.pi.filename)

        SoM.num_anim = num_anim
        SoM.sep_thresh = 0.9 if sep_thresh is None else sep_thresh
        SoM.margin = margin
        SoM.minpix = minpix

        logger.debug(f"num_anim={num_anim}, sep_thresh={sep_thresh}, margin={margin}, minpix={minpix}")

        pi = self.pi
        imz = SoM.z_compress_pet(pi)
        blobs_labels, num = SoM.detect_animals(imz)
        self.blob_labels = blobs_labels

        if num_anim is not None:
            if num < num_anim:
                logger.info('split_mice detected less regions ({}) than indicated animals({}), attempting to compensate'.
                      format(num, num_anim))
                while num < num_anim and self.sep_thresh < 1:
                    self.sep_thresh += 0.01
                    blobs_labels, num = SoM.detect_animals(imz)
                if num < num_anim:
                    logger.info('compensation failed')
                    pi.clean_cuts()
                    pi.unload_image()
                    return 1
            rects = measure.regionprops(blobs_labels)
            if num > num_anim:
                rects.sort(key=lambda p: p.area, reverse=True)
                rects = rects[:num_anim]
        else:
            rects = SoM.get_valid_regs(blobs_labels)
            if len(rects) > 4:
                logger.info('detected {}>4 regions, attempting to compensate'.format(len(rects)))
                inc = self.minpix * 0.1
                while len(rects) > 4:
                    self.minpix += inc
                    rects = SoM.get_valid_regs(blobs_labels)
        self.cuts = SoM.split_coords(imz, rects)

        # adjust the size of the cuts if img_size is specified.
        # helpful for keeping the same image size across multiple scans.
        if img_size is not None:
            for cut in self.cuts:
                cut['rect'].adjust_to_size(img_size)

        save_analyze_dir = outdir if save_analyze else None
        SoM.add_cuts_to_image(pi, self.cuts, desc_map, save_analyze_dir, dicom_metadata)

        # write the images.
        if outdir is not None:
            SoM.write_images(pi, outdir, zip=zip)

        if output_qc:
            im = SoM.qc_image(pi, blobs_labels, self.cuts, outdir, desc_map)
            # debug
            # SoM.display_pil_image(im)

        # pi.clean_cuts()
        # pi.unload_image()
        return 0

    @staticmethod
    def standardize_range(im, ignore_min=False, pct=5):
        mx = np.percentile(im, 100 - pct)
        mn = 0 if ignore_min else np.percentile(im, pct)
        im1 = im
        im1[im > mx] = mx
        im1[im < mn] = mn
        rng = mx - mn
        logger.debug(f'min,max,rng: {mn}, {mx}, {rng}')
        im1 = ((im1 - mn) / rng) * 255
        logger.debug(f'min_new,max_new: {np.min(im1)}, {np.max(im1)}')
        return im1

    @staticmethod
    def qc_image(pi, labels, rects_dict, outdir, desc_map):
        imz, img_type, alpha = None, None, None

        if isinstance(pi, PETImage):
            imz = SoM.z_compress_pet(pi)
            img_type = 'PET'
            imz /= np.max(imz)
            linwid = 1
            alpha = 0.1
            pct = 5

        elif isinstance(pi, CTImage):
            imz = SoM.z_compress_ct(pi, SoM.sep_thresh, binary=False)
            img_type = 'CT'
            pct = 2
            imz = SoM.standardize_range(imz, pct=pct)
            imz /= np.max(imz)
            linwid = 3
            alpha = 0.3
            # SoM.display_pil_image(Image.fromarray(imz).convert('RGB'))

        elif isinstance(pi, DicomImage):
            if pi.modality == 'CT':
                imz = SoM.z_compress_ct(pi, SoM.sep_thresh, binary=False)
                img_type = 'CT'
                pct = 2
                imz = SoM.standardize_range(imz, pct=pct)
                imz /= np.max(imz)
                linwid = 3
                alpha = 0.3
                # SoM.display_pil_image(Image.fromarray(imz).convert('RGB'))
            elif pi.modality == 'PT' or pi.modality == 'PET':
                imz = SoM.z_compress_pet(pi)
                img_type = 'PET'
                imz /= np.max(imz)
                linwid = 1
                alpha = 0.1
                pct = 5
            else:
                logger.error(f"QC not supported for dicom modality: {pi.modality}")
                return
        else:
            logger.error(f"Unknown image type: {type(pi)}. Cannot perform qc.")
            return

        if imz is None:
            logger.info('qc_image: unknown image type')
            return

        color_map = {
            'l': 'lightblue',
            'r': 'red',
            'ctr': 'violet',
            'lb': 'violet',
            'rb': 'lightgreen',
            'lt': 'lightblue',
            'rt': 'red'
        }

        colors = [color_map[rd['desc']] if rd['desc'] in color_map else 'yellow' for rd in rects_dict]
        imz_qc_arr = np.uint8(255 * skimage.color.label2rgb(labels, image=imz, bg_label=0, alpha=alpha, colors=colors))
        imz_qc = Image.fromarray(imz_qc_arr).convert('RGB')

        # make individual axial images.
        ax_ims_pil, ax_ims_lbl = [], []

        d = ImageDraw.Draw(imz_qc)

        for i in range(0, len(rects_dict)):
            rd = rects_dict[i]
            r = rd['rect']
            im0 = r.subimage(imz_qc_arr)  # logger.info('axial subimage ',i,', ',im0.shape)
            ax_ims_pil += [Image.fromarray(im0).convert('RGB')]
            ax_ims_lbl += [rd['desc']]
            logger.info(ax_ims_lbl)
            d.rectangle(((r.ylt, r.xlt), (r.yrb, r.xrb)), outline=colors[i], width=linwid)
            # d.text((r.ylt, r.xlt), rd['desc'], fill=colors[i])

        sag_ims = [SoM.get_sag_image(pi.cuts[i].img_data) for i in range(len(pi.cuts))]
        sag_ims_pil = []
        for i, im in zip(range(0, len(rects_dict)), sag_ims):
            im1 = SoM.standardize_range(im, pct=pct)
            imp = Image.fromarray(im1).convert('RGB')
            sag_ims_pil += [imp]
            # logger.info('sagittal subimage ',i,', ',np.swapaxes(im1,0,1).shape)
            # code to combine axial and sagittal images, and save subimage.
            individual_qc_im = SoM.combine_images(
                [ax_ims_pil[i], Image.fromarray(np.swapaxes(im1, 0, 1)).convert('RGB')])
            if img_type == 'PET':
                w, h = individual_qc_im.size
                individual_qc_im = individual_qc_im.resize((w * 3, h * 3), resample=Image.BILINEAR)
            fnamei = outdir + '/qc/' + 'qc_' + desc_map[ax_ims_lbl[i]] + '.png'

            if not os.path.exists(f"{outdir}/qc"):
                os.makedirs(f"{outdir}/qc")

            logger.info(f"writing {fnamei}")
            # create the file if it doesn't exist
            open(fnamei, 'a').close()
            individual_qc_im.save(fnamei, 'png')
            # SoM.display_pil_image(imp)

        # sag_ims_pil= [ Image.fromarray(im).convert('RGB') for im in sag_ims ]
        # SoM.display_pil_image(sag_ims_pil[0])

        si_dims = [sag_ims[0].shape]
        sag_im = SoM.combine_images(sag_ims_pil)
        d1 = ImageDraw.Draw(sag_im)
        off = 0
        for i in range(len(sag_ims)):
            sh = sag_ims[i].shape
            d1.rectangle([off, 0, off + sh[1] - 1, sh[0] - 1], outline=colors[i], width=linwid)
            off += sh[1]

        fname = outdir + '/qc/' + 'split_qc.png'

        if not os.path.exists(f"{outdir}/qc"):
            os.makedirs(f"{outdir}/qc")

        qc_im = SoM.combine_images([imz_qc, sag_im])
        if img_type == 'PET':
            w, h = qc_im.size
            qc_im = qc_im.resize((w * 3, h * 3), resample=Image.BILINEAR)
        logger.info(f"writing {fname}")
        qc_im.save(fname, 'png')

        pi.qc_outputs = f'{outdir}/qc'

        return qc_im
        # end of SoM class
