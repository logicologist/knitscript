grammar KnitScript;

document: patterns+=patternDef* EOF;

patternDef: 'pattern' ID ':' lines+=line+;

line: (row | block) '.';

block: calls+=call (',' calls+=call)*;
call: ID;

row: 'row:' stitchList;

stitchRepeat: fixedStitchRepeat | expandingStitchRepeat | stitch;
fixedStitchRepeat
    : stitch count=NATURAL
    | '(' stitchList ')' count=NATURAL;
expandingStitchRepeat
    : (stitch | '(' stitchList ')') 'to end'
    | (stitch | '(' stitchList ')') 'to last' toLast=NATURAL;
stitchList: stitches+=stitchRepeat (',' stitches+=stitchRepeat)*;

stitch: ID;

ID: [A-Za-z] [A-Za-z0-9]*;
NATURAL: [1-9] [0-9]*;
WHITESPACE: [ \r\n] -> skip;
