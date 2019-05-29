grammar KnitScript;

document: patterns+=patternDef* EOF;

patternDef: 'pattern' ID ('(' paramList ')')? ':' lines+=line+;
paramList: params+=ID (',' params+=ID)*;

line: (row | block) '.';

block: calls+=call (',' calls+=call)*;
call: ID ('(' argList ')')?;
argList: args+=expr (',' args+=expr)*;

row: 'row:' stitchList;

stitchRepeat: fixedStitchRepeat | expandingStitchRepeat | stitch;
fixedStitchRepeat
    : stitch count=expr
    | '(' stitchList ')' count=expr;
expandingStitchRepeat
    : (stitch | '(' stitchList ')') 'to end'
    | (stitch | '(' stitchList ')') 'to last' toLast=expr;
stitchList: stitches+=stitchRepeat (',' stitches+=stitchRepeat)*;

stitch: ID;

expr: variable | natural;
variable: ID;
natural: NATURAL;

ID: [A-Za-z] [A-Za-z0-9]*;
NATURAL: [1-9] [0-9]*;
WHITESPACE: [ \r\n] -> skip;
