pattern ninePatches (p1, p2, p3, p4, p5, p6, p7, p8, p9)
  p1, p4, p7.
  p8, p2, p5.
  p6, p9, p3.
end

pattern blanket (m, n)
  row: CO 48.
  repeat n
    ninePatches (fill(garter,16,16), fill(stst,16,16), fill(reverseStst,16,16),
      fill(rib (1, 1),16,16), fill(seed,16,16), fill(basketweave,16,16),
      fill(seersucker,16,16), fill(slippedWaves,16,16), fill(stripes,16,16)) m.
  end
  row: BO 48.
end

show (blanket (1, 1))

