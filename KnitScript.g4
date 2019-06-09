grammar KnitScript;

document: stmts+=stmt* EOF;
stmt: using | patternDef | call;

using: 'using' names+=ID (',' names+=ID)* 'from' module=ID;

patternDef: 'pattern' ID ('(' paramList ')')? items+=item+ 'end';
paramList: params+=ID (',' params+=ID)*;

item
    : (row | block) '.'
    | rowRepeat;

rowRepeat: 'repeat' times=expr items+=item+ 'end';
row: 'row' side? ':' (stitchList | 'empty');
side: 'RS' | 'WS';

block: patternList;

patternRepeat: fixedPatternRepeat | call;
fixedPatternRepeat
    : pattern=call times=expr
    | '(' patternList ')' times=expr;
patternList: patterns+=patternRepeat (',' patterns+=patternRepeat)*;

stitchRepeat: fixedStitchRepeat | expandingStitchRepeat | stitch;
fixedStitchRepeat
    : stitch times=expr
    | '(' stitchList ')' times=expr;
expandingStitchRepeat
    : (stitch | '(' stitchList ')') 'to end'
    | (stitch | '(' stitchList ')') 'to last' toLast=expr;
stitchList: stitches+=stitchRepeat (',' stitches+=stitchRepeat)*;

stitch: ID;

expr: variable | call | natural | string;
variable: ID;
call: ID ('(' args+=expr (',' args+=expr)* ')')?;
natural: NATURAL;
string: STRING;

ID: [_A-Za-z] [_A-Za-z0-9]*;
NATURAL: [1-9] [0-9]* | '0';
STRING: '"' ~('"')* '"';
WHITESPACE: [ \r\n] -> skip;
COMMENT: '--' ~[\r\n]* -> skip;
