//command line parameters
var arguments = process.argv.slice(2);
var script = null;
var fs = require('fs');
if(arguments.length == 1){
  console.log('read script from file '+arguments[0]);
  script = fs.readFileSync(arguments[0], 'utf8');
}
else{
  script = 'var answer = 42; answer += "str";';
}

var esprima = require('esprima');
var escodegen = require('escodegen');
/* Codes from project ast-traverse */
var traverse = function (root, options) {
  "use strict";
  options = options || {};
  var pre = options.pre;
  var post = options.post;
  var skipProperty = options.skipProperty;

  function visit(node, parent, prop, idx) {  
    if (!node || typeof node.type !== "string") {
      return;
    }
    var res = undefined;
    if (pre) {
      res = pre(node, parent, prop, idx);
    }

    if (res !== false) {
      for (var prop in node) {
        if (skipProperty ? skipProperty(prop, node) : prop[0] === "$") {
          continue;
        }
        var child = node[prop];
        
        if (Array.isArray(child)) {
          for (var i = 0; i < child.length; i++) {
              visit(child[i], node, prop, i);
          }
        } else {
            visit(child, node, prop);
        }
      }
    }

    if (post) {
        post(node, parent, prop, idx);
    }
  }
  visit(root, null);
};

//directly display parsing results
var ast = esprima.parse(script);
var result = JSON.stringify(ast, null, 2);
console.log(result);

var CSPAutoGenVisitor = function(tree) {
  var ast = tree;
  var indent = 0;
  var id = 1;
  var string_count = 0;
  var number_count = 0;
  var boolean_count = 0;
  
  //helper methods
  //return value:
  //  atom: 'string', 'null', 'RegExp', 'number' and 'boolean'
  //  complex: 'array' and 'object'
  //  other: null and 'non-data-type'
  var get_data_node_type = function (node) {
    if (!node || typeof node.type !== "string") {
      return null;
    }
    if (node.type === 'Literal') {
      var type = typeof node.value;
      if (type !== 'object'){
        return type;
      }
      else if(node.value instanceof RegExp){
        return 'RegExp';
      }
      else {
        return 'null';
      }
    }
    else if (node.type === 'ObjectExpression') {
      return 'object';
    }
    else if (node.type === 'ArrayExpression') {
      return 'array';
    }
    else {
      return 'non-data-type';
    }
  };
  var convert_arr_to_non_nested_obj =
    function(arr, result, level) {
    if (! arr['elements']) {
      console.warn("the array doesn't have elements");
      return result;
    }
    for (var index in arr['elements']){
      var elem = arr['elements'][index];
      if (!elem || typeof elem.type !== "string") {
        continue;
      }
      
      var type = get_data_node_type(elem);
      var sub_result = {};
      switch (type) {
        case 'boolean':
          if (! result['CSP_Boolean']) {
            result['CSP_Boolean'] = [elem.value];
          }
          else {
            result['CSP_Boolean'].push(elem.value);
          }
          break;
        case 'string':
          var label = 'CSP_String_'+level;
          if (! result[label]) {
            result[label] = [elem.value];
          }
          else {
            result[label].push(elem.value);
          }          
          break;
        case 'number':
          //console.log("debug: "+elem.value);
          if (! result['CSP_Number']) {
            result['CSP_Number'] = [elem.value];
          }
          else {
            result['CSP_Number'].push(elem.value);
          }
          break;
        case 'null':
          if (! result['CSP_Null']) {
            result['CSP_Null'] = [elem.value];
          }
          else {
            result['CSP_Null'].push(elem.value);
          }
          break;
        case 'RegExp':
          if (! result['CSP_RegExp']) {
            result['CSP_RegExp'] = [elem.value];
          }
          else {
            result['CSP_RegExp'].push(elem.value);
          }
          break;
        case 'object':
          convert_obj_to_non_nested_obj(elem, sub_result, level+1);
          combine_two_objs(result, sub_result);
          break;
        case 'array':
          convert_arr_to_non_nested_obj(elem, sub_result, level+1);
          //console.log('subarray:'+sub_result);
          combine_two_objs(result, sub_result);
          break;
        case 'non-data-type':
          if (! result['CSP_GAST']) {
            result['CSP_GAST'] = [elem.type];
          }
          else {
            result['CSP_GAST'].push(elem.type);
          }
          break;
        default:
          console.warn('unknown elem for array '+type+' '+elem.type);
          break;
      }
    }
  };

  var convert_obj_to_non_nested_obj = 
    function(obj, result, level) {
  };

  //assume the two params are non-nested
  var combine_two_objs =
    function (master_obj, elem_obj){
    for (var prop in elem_obj) {
      if (master_obj[prop]) {
        master_obj[prop] = master_obj[prop].concat(elem_obj[prop]);
      }
      else {
        master_obj[prop] = elem_obj[prop];
      }
    }
  };

  //visit methods
  var visit_hanlders = {};
  visit_hanlders.visitLiteral = function(node, parent, prop, idx){
    if (typeof node.value === 'string') {
      node.value = 'CSP_String';
      string_count++;
    }
    else if(typeof node.value === 'number') {
      node.value = 'CSP_Number';
      number_count++;
    }
    else if(typeof node.value === 'boolean') {
      node.value = 'CSP_Boolean';
      boolean_count++;
    }
    return true;
  };
  visit_hanlders.visitObjectExpression = 
    function(node, parent, prop, idx) {
    return true;
  };
  visit_hanlders.visitArrayExpression = 
    function(node, parent, prop, idx) { 
      var non_nested_obj = {};
      convert_arr_to_non_nested_obj(node,non_nested_obj,0);
      for (var k in non_nested_obj) {
        console.log('array_elem: '+k+' val:'+non_nested_obj[k]);
      }
      return false;
  };

  var visit = function(){
    traverse(ast, {
      pre: function(node, parent, prop, idx) {
        var method = 'visit'+node.type;
        var cont = true;
        console.log(Array(indent + 1).join(" ") + node.type +
          ' value:'+node.value+' value type:'+get_data_node_type(node));
        if (visit_hanlders.hasOwnProperty(method)) {
          //console.log(Array(indent + 1).join(" ") + 
          //  node.type +' value:'+node.value+' value type:');
          cont = visit_hanlders[method](node, parent, prop, idx);
        }
        
        indent += 2;
        return cont;
      },
  
      post: function(node) {
        indent -= 2;
      }
    });
  }; //visit

  return {
    visit : visit
  };
};

var visitor = CSPAutoGenVisitor(ast);
visitor.visit();

//generate new source codes
var new_sc = escodegen.generate(ast);
console.log(new_sc);

//var result = JSON.stringify(ast, null, 2);
//console.log(result);