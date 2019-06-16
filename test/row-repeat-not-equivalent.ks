pattern garterTest
  row: CO 1.
  repeat 2
    garter.
  end
  garter.
  garter.
  row: BO 1.
end

pattern forceUnroll
  row: CO 1.
  row: K.
  row: K.
  row: K.
  row: K.
  row: BO 1.
end

pattern main
  garterTest, forceUnroll.
end
