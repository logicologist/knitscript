grammar KnitScript;

pattern: rows+=row+ EOF;
row: stitches+=stitch (',' stitches+=stitch)* '.';
stitch: symbol=ID;

ID: [A-Za-z] [A-Za-z0-9]*;
WS: [ \r\n] -> skip;
