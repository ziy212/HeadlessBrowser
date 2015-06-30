var express = require('express');
var querystring = require('querystring');
var urlParse = require('url');
var bodyParser = require('body-parser');
var util = require('util');

var mongo = require('mongodb');
var monk = require('monk');
var db = monk('localhost:27017/webcontents');

var app = express();
app.use(bodyParser({limit: '50mb'}));
app.use(bodyParser.json() );

var standardizeURL = function (url) {
	try{
		var url = querystring.unescape(url);
		var o = urlParse.parse(url)
		var new_url = o.protocol+'//'+o.host+o.path;
		//console.log(new_url);
		return new_url;
	}
	catch (e) {
		console.log("failed parse url "+e);
		return null;
	}

};
app.use(function(req,res,next){
    req.db = db;
    next();
});

app.post('/api/web-contents/store', function (req, res) {
	if ( !req.body.url || !req.body.contents ) {
		res.json({success : false});
	}
  res.json({
  	success : true,
  	url : req.body.url,
  	size : req.body.contents.length});
 
  try{
  	var url = standardizeURL(req.body.url);
	  var contents = req.body.contents;
	  var collection = db.get('contentscollection');
	  collection.insert({
	  	url : url,
	  	contents : contents
	  }, function (err, doc) {
	    if (err) {
	        console.log("[FAIL] failed to insert into DB: "+url);
	    }
	    else {
	        console.log("[SUCC] inserted into DB "+url);
	    }} );
  }
  catch (e) {
  	console.log("[FAIL] failed to process req "+e);
  }
});

app.post('/api/web-contents/fetch', function (req, res){
	if ( !req.body.url ) {
		res.json({success : false});
	}
	try{
  	var url = standardizeURL(req.body.url);
  	console.log("  [DEBUG] fetch contents of url: "+url);
  	var index;
	  var collection = db.get('contentscollection');
	  collection.find({
	  	url : url}, function (err, docs) {
	    if (err) {
	        console.log("[FAIL] failed to fetch contents for "+url);
	        res.json({
  					success : false
  				});
	    }
	    else {
	        console.log("[SUCC] " + docs.length +' items');
	        for (index in docs) {
	        	docs[index].url = querystring.escape(docs[index].url);
	        	console.log("  [DEBUG] "+docs[index].url+" "+docs[index].contents.length);
	        }
	        res.json({
  					success : true,
  					result : JSON.stringify(docs)
  				});
	    }} );
  }
  catch (e) {
  	console.log("[FAIL] failed to process req "+e);
  	res.json({ success : false });
  }	

});
//standardizeURL("http%3A%2F%2Fwww.cnn.com");
//standardizeURL("http://www.cnn.com/");
//standardizeURL("http://www.cnn.com/abcd/eed/ffs.html?dsd=22&dsds=233&dsdsd");

var server = app.listen(4040, function () {

  var host = server.address().address;
  var port = server.address().port;

  console.log('Example app listening at http://%s:%s', host, port);

});
