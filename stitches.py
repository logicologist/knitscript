

def throwError(msg):
    return lambda(raise Exception(msg))


class Stitch:
    def __init__(self):
        self.inverseWS = throwError("Cannot reverse generic stitch")
        # Left-right inverses, for reversing, go here
    def make_reverse(self):
        return self.inverseWS()


class Knit(Stitch):
    def __init__(self):
        self.inverseWS = Purl

class Purl(Stitch):
    def __init__(self):
        self.inverseWS = Knit

class YarnOver(Stitch):
    def __init__(self):
        self.inverseWS = YarnOver

class Knit2Tog(Stitch):
    def __init__(self):
        self.inverseWS = SlipSlipPurl

class SlipSlipKnit(Stitch):
    def __init__(self):
        self.inverseWS = Purl2Tog

class Purl2Tog(Stitch):
    def __init__(self):
        self.inverseWS = SlipSlipKnit

class SlipSlipPurl(Stitch):
    def __init__(self):
        self.inverseWS = Knit2Tog





class Pattern:
    def __init__(self, arg):
        self.stitches = []



