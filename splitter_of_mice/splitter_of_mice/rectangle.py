"""
Rectangle manipulation
"""
import numpy as np
import logging

logger = logging.getLogger(__name__)


class Rect:

    def overlaps(self, other):
        a, b = self, other
        xlt = max(min(a.xlt, a.xrb), min(b.xlt, b.xrb))
        ylt = max(min(a.ylt, a.yrb), min(b.ylt, b.yrb))
        xrb = min(max(a.xlt, a.xrb), max(b.xlt, b.xrb))
        yrb = min(max(a.ylt, a.yrb), max(b.ylt, b.yrb))
        return xlt < xrb and ylt < yrb

    def intersection(self, other):
        a, b = self, other
        xlt = max(min(a.xlt, a.xrb), min(b.xlt, b.xrb))
        ylt = max(min(a.ylt, a.yrb), min(b.ylt, b.yrb))
        xrb = min(max(a.xlt, a.xrb), max(b.xlt, b.xrb))
        yrb = min(max(a.ylt, a.yrb), max(b.ylt, b.yrb))
        if xlt <= xrb and ylt <= yrb:
            return type(self)(xlt, ylt, xrb, yrb)

    def wid(self):
        return self.xrb - self.xlt

    def ht(self):
        return self.yrb - self.ylt

    def ctr(self):
        return self.xlt + self.wid() * .5, self.ylt + self.ht() * .5

    def expand(self, m):
        self.xlt -= m[0]
        self.xrb += m[0]
        self.ylt -= m[1]
        self.yrb += m[1]

    def adjust_to_size(self, sz):
        sz0, x0, x1 = np.array(sz), np.array([self.xlt, self.ylt]), np.array([self.xrb, self.yrb])
        d = (sz0 - (x1 - x0)) * .5;
        x0n = (x0 - d).astype(int);
        x1n = x0n + sz0
        self.xlt, self.ylt, self.xrb, self.yrb = x0n[0], x0n[1], x1n[0], x1n[1]

    def adjust_to_center(self, cx, cy):
        print('adjust to center: ', str(cx), str(cy))
        print(str(self))
        c, x0, x1 = np.array([cx, cy]), np.array([self.xlt, self.ylt]), np.array([self.xrb, self.yrb])
        c0 = np.array(self.ctr())
        d = (c - c0).astype(int)
        x0 += d;
        x1 += d;
        self.xlt, self.ylt, self.xrb, self.yrb = x0[0], x0[1], x1[0], x1[1]
        print('adusted,', str(self))

    def rescale(self, scale_x, scale_y):
        self.xlt = int(round(self.xlt * scale_x))
        self.xrb = int(round(self.xrb * scale_x))
        self.ylt = int(round(self.ylt * scale_y))
        self.yrb = int(round(self.yrb * scale_y))

    def __str__(self):
        return "Rectangle, wid={}, ht={}, ctr=({},{}), l,t,r,b=({},{},{},{})".format(
            self.wid(), self.ht(), self.ctr()[0], self.ctr()[1], self.xlt, self.ylt, self.xrb, self.yrb)

    @staticmethod
    def union_list(rects):
        if len(rects) < 1: return None
        out = rects[0]
        for i in range(len(rects)):
            out = out.union(rects[i])
        return out

    def union(self, other):
        a, b = self, other
        return type(self)(verts=[min(a.xlt, b.xlt), min(a.ylt, b.ylt), max(a.xrb, b.xrb), max(a.yrb, b.yrb)])

    def __init__(self, bb=None, verts=None, label=None):
        if bb is not None:
            self.xlt, self.ylt, self.xrb, self.yrb = bb[0], bb[1], bb[2], bb[3]
        if verts is not None:
            self.xlt, self.ylt, self.xrb, self.yrb = verts[0], verts[1], verts[2], verts[3]

        self.label = label

    def __copy__(self):
        return type(self)(bb=[self.xlt, self.ylt, self.xrb, self.yrb])

    def __deepcopy__(self, memodict={}):
        return type(self)(bb=[self.xlt, self.ylt, self.xrb, self.yrb])

    def area(self):
        return float(self.xrb - self.xlt) * (self.yrb - self.ylt)

    def pt_inside(self, pt):
        return pt[0] > self.xlt and pt[0] < self.xrb and pt[1] > self.ylt and pt[1] < self.yrb

    # for a pt inside, return its quadrant.
    def quadrant(self, pt):
        c = self.ctr()
        tl, tr = Rect(verts=[self.xlt, self.ylt, c[0], c[1]]), Rect(verts=[self.xlt, c[1], c[0], self.yrb])
        bl, br = Rect(verts=[c[0], self.ylt, self.xrb, c[1]]), Rect(verts=[c[0], c[1], self.xrb, self.yrb])
        if tl.pt_inside(pt):
            return 'lt'
        elif tr.pt_inside(pt):
            return 'rt'
        elif bl.pt_inside(pt):
            return 'lb'
        elif br.pt_inside(pt):
            return 'rb'
        else:
            return 'ot'

    def subimage(self, img):
        xl, xr, yt, yb = int(round(max(self.xlt, 0))), int(round(min(self.xrb, img.shape[0] - 1))), \
            int(round(max(self.ylt, 0))), int(round(min(self.yrb, img.shape[1] - 1)))
        return img[xl:xr, yt:yb]

    def significant_intersection(self, other, ratio=0.5):
        a, b = self, other
        c = a.intersection(b)
        if c is None:
            return False
        s1, s2, s3 = a.area(), b.area(), c.area()
        if s3 != 0:
            return (min(s1, s2) / s3 >= ratio)
        else:
            return False
