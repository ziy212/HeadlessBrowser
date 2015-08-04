var mongo = require('mongodb');
var monk = require('monk');
var db = monk('localhost:27017/webcontents');
var fs = require('fs');
var querystring = require('querystring');
var urlParse = require('url');

var standardizeURL = function (url) {
	try{
		var url = querystring.unescape(url);
		var o = urlParse.parse(url)
		var new_url = o.protocol+'//'+o.host+o.path;
		//console.log(new_url);
    var is_google = o.host.toLowerCase().indexOf("google.com")
    if(is_google != -1){
      return url;
    }
		return new_url;
	}
	catch(e) {
		console.log("failed parse url "+e);
		return null;
	}

};
var arguments = process.argv.slice(2);
var collection1 = db.get('contentscollection');
var collection2 = db.get('inlinescripts');
var collection3 = db.get('scripthosts');
console.log(arguments[0]);

fs.readFile(arguments[0], 'utf8', function (err,data) {
  if (err) {
    return console.log(err);
  }
  var urls = data.split('\n');
  for(var i in urls){
  	var url = standardizeURL(urls[i]);
  	if(url === null){
  		continue;
  	}
  	//console.log(i+' '+url);
  	var u = url;
  	collection1.remove({url:url}, function(err, doc){
  		if (err){
  			console.log('failed remove contents of '+u+' '+err);
  			return;
  		}
  		console.log('succeed remove contents of '+u+ ' '+doc);
  	});
  	collection2.remove({url:url}, function(err, doc){
  		if (err){
  			console.log('failed remove inlines of '+u+' '+err);
  			return;
  		}
  		console.log('succeed remove inlines of '+u+ ' '+doc);
  	});
  	collection3.remove({url:url}, function(err, doc){
  		if (err){
  			console.log('failed remove scripthosts of '+u+' '+err);
  			return;
  		}
  		console.log('succeed remove scripthosts of '+u+ ' '+doc);
  	});
  }
});
