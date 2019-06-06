grammar KnitScript;

document: usings+=usingStmt* patterns+=patternDef* EOF;

usingStmt: 'using' patternNames+=ID (',' patternNames+=ID)* 'from' filename=ID;

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
    : call times=expr
    | '(' patternList ')' times=expr;
patternList: patterns+=patternRepeat (',' patterns+=patternRepeat)*;

call: ID ('(' argList ')')?;
argList: args+=expr (',' args+=expr)*;

stitchRepeat: fixedStitchRepeat | expandingStitchRepeat | stitch;
fixedStitchRepeat
    : stitch times=expr
    | '(' stitchList ')' times=expr;
expandingStitchRepeat
    : (stitch | '(' stitchList ')') 'to end'
    | (stitch | '(' stitchList ')') 'to last' toLast=expr;
stitchList: stitches+=stitchRepeat (',' stitches+=stitchRepeat)*;

stitch: ID;

expr: variable | natural;
variable: ID;
natural: NATURAL;

ID: [A-Za-z] [A-Za-z0-9]*;
NATURAL: [1-9] [0-9]* | '0';
WHITESPACE: [ \r\n] -> skip;
COMMENT: '--' ~[\r\n]* -> skip;
