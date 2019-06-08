pattern hello (p, q)
  p (5).
  q.
end

pattern goodbye (n)
  repeat n
    row: K, P, K.
  end
end

pattern main
  row: CO 3.
  hello (goodbye, goodbye (3)).
  row: BO 3.
end
