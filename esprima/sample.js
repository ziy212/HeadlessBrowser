var x = 44;
var y = {a:1, b:2, c:x, d:'string', e:[1,2,'3',4,{aa:2},fun()+1, [8,'str2']], f:{aa:11,bb:'strbb'}};
var z= new Object({m:1});
var d = Object.create({m:1});
var re = /ab+c/;
fun(x,y.c+y.a);