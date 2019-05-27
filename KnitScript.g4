grammar KnitScript;

document: patterns+=patternDef* EOF;

patternDef: 'pattern' ID ('(' paramList ')')? ':' rows+=row+;
paramList: params+=ID+;

row: stitchList '.';

stitchRepeat: fixedStitchRepeat | expandingStitchRepeat | stitch;
fixedStitchRepeat
    : stitch count=NATURAL
    | '(' stitchList ')' count=NATURAL;
expandingStitchRepeat
    : (stitch | '(' stitchList ')') ' to end'
    | (stitch | '(' stitchList ')') ' to last ' toLast=NATURAL;
stitchList: stitches+=stitchRepeat (',' stitches+=stitchRepeat)*;

stitch: ID;

ID: [A-Za-z] [A-Za-z0-9]*;
NATURAL: [1-9] [0-9]*;
WS: [ \r\n] -> skip;
