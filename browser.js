
var page = require('webpage').create(),
    system = require('system'),
    server = require('webserver').create(),
    service, listenPort, 
    browsingHandler, address,
    requestCount = 0, responseCount = 0,
    displayObject;

/* Settings */
page.settings.userAgent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:38.0) Gecko/20100101 Firefox/38.0';
listenPort = 4000;

/* Running listening service */
service = server.listen(listenPort, function (request, response) {
    var payload, error;
    console.log('Request received at ' + new Date());

    response.headers = {
        'Cache': 'no-cache',
        'Content-Type': 'text/plain;charset=utf-8'
    };
    try {
        payload = JSON.parse(request.postRaw);
        if (! payload.job ) {
          error = new Error();
          error.name = "BadJobError";
          throw error;
        }
        if (payload.job.toLowerCase() === "open"){
          browsingHandler(payload.url);
        }
        response.statusCode = 200;
        response.write("received: "+JSON.stringify(payload, null, 4));
    }
    catch (e) {
        response.statusCode = 400;
        response.write("bad request: "+e.name);
    }
    response.close();
});
console.log("PhantomJS listens request on port "+listenPort);

/* Browsing method */
browsingHandler = function (url) {
    console.log("start browsing: "+url);
    page = require('webpage').create();
     
    var landing_page = url;

    page.onResourceRequested = function (req) {
        requestCount++;
        //console.log('requested: '+count+" "+ JSON.stringify(req, undefined, 4));
    };

    page.onResourceReceived = function (res) {
        //console.log('received: ' + JSON.stringify(res, undefined, 4));
        responseCount++;
        if (res.redirectURL) {
            landing_page = res.redirectURL;
        }
        //console.log(res.redirectURL);
    };

    page.open(address, function (status) {
        if (status !== 'success') {
            console.log('FAIL to load the address');
        }
        var content = page.content;
        console.log("done rendering: " + url +
          " landing_page: "+landing_page);
        //console.log('Content: ' + content);
        //phantom.exit();
    });
};

var displayObject = function (obj) {
  var item;
  for (item in obj) {
    if (obj.hasOwnProperty(item)) {
        console.log("KEY: "+ item+" VAL:"+obj[item]);
    }
  }
};

/* Testing codes for browsing Handler */
if (system.args.length === 1) {
    console.log('Usage: netlog.js <some URL>');
    phantom.exit(1);
}
else {
    address = system.args[1];
    browsingHandler(address);
}