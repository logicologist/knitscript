pattern interlude
  row: K, P to last 1, K.
end

pattern basicScarf (n)
  row: CO 41.
  repeat n
    row: K, (YO, K 3, SL, K2TOG, PSSO, K 3, YO, K) to end.
    interlude.
    row: K, (K, YO, K 2, SL, K2TOG, PSSO, K 2, YO, K 2) to end.
    interlude.
    row: K, (K 2, YO, K, SL, K2TOG, PSSO, K, YO, K 3) to end.
    interlude.
    row: K, (K 3, YO, SL, K2TOG, PSSO, YO, K 4) to end.
    interlude.
  end
  row: BO to end.
end

note ("This is an example of a simple knitting pattern with a parameter.")
show (basicScarf (5), "Basic scarf with 5 repeats")
