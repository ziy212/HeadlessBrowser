var queue = require('./Queue'),
  system = require('system'),
  server = require('webserver').create(),
  service, listenPort, 
  browsingHandler, address, userAgent, timeout,
  displayObject, maxBrowserInstance;

/* Settings */
listenPort = 4000;
maxBrowserInstance = 1;
userAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:38.0) Gecko/20100101 Firefox/38.0";
timeout = 5000;


/* Task Manager */
var taskManager = (function (){
  var max_instances, user_agent,
    task_queue = new queue(),
    page = null;
    configure, post_task, start_tasks, timeout,
    open_url, open_url_callback;

  configure = function(settings) {
    max_instances = settings.max_instances;
    user_agent = settings.user_agent;
    timeout = settings.timeout;
  };

  post_task = function (task) {
    task_queue.enqueue(task);
    console.log("adding a browsing task: "+task_queue.getLength());
    start_tasks();
  };

  open_url_callback = function (result) {
    var content;
    try{
      if (result.status !== 'success') {
        console.log('[FAIL] to load the address:'+result.url);
      }
      else {
        content = result.content;
        console.log("[SUCCEED] to load the address: " + result.url +
        " contnet-size: "+result.content.length,
        " failed objects: "+ result.failed_obj_count,
        " landing_page: "+result.landing_page);
        //console.log(result.content);
      }
      
      if (task_queue.getLength() > 0) {
        start_tasks();
      }
    }
    catch (err) {
      console.log("[PHANTOM_ERR] error in open_url_callback "+err);
    }
    finally {
      console.log("task_queue_size "+ task_queue.getLength());
    }
  };

  //this method creates and closes the page instance
  open_url = function (url) {
    var page = require('webpage').create(),
      landing_page = url, content, timeout_count = 0,
      request_count = 0, response_count = 0;

    page.settings.resourceTimeout = 5000;
    page.settings.userAgent = user_agent;
    page.onResourceRequested = function (req) {
      //console.log("request:"+req.url);
      request_count++;
    };

    page.onResourceReceived = function (res) {
      response_count++;
      if (res.redirectURL) {
          landing_page = res.redirectURL;
      }
    };

    page.onResourceTimeout = function (e) {
      //console.log(e.errorCode);   // it'll probably be 408 
      //console.log(e.errorString); // it'll probably be 'Network timeout on resource'
      //console.log(e.url);         // the url whose request timed out
      timeout_count++;
    };

    console.log("start browsing: "+url);
    try{
      page.open(url, function (status) {
        page.render('github.png');
        open_url_callback({
          status : status,
          url : url,
          landing_page : landing_page,
          request_count : request_count,
          response_count : response_count,
          failed_obj_count : timeout_count,
          content : page.content.slice(0)
        });
        page.close();
      });
    }
    catch (err) {
      console.log("[PHANTOM_ERR] error in open "+url+" error:"+err);
    }
    
  };
  
  start_tasks = function () {
    var task;
    while (task_queue.getLength() > 0){
      if (page === null) {
        task = task_queue.dequeue();
        open_url(task.url);
      }
      else {
        console.log("cannot start task now: runnning_instances achieve maximum");
        break;
      }
    }
  };

  return {
    configure : configure,
    post_task : post_task
  };
})();

/* Utilities */
var displayObject = function (obj) {
  var item;
  for (item in obj) {
    if (obj.hasOwnProperty(item)) {
        console.log("KEY: "+ item+" VAL:"+obj[item]);
    }
  }
};

/* Testing */
if (system.args.length === 1) {
    
}
else {
  address = system.args[1];
  taskManager.configure({
    max_instances : maxBrowserInstance,
    timeout : timeout,
    user_agent : userAgent });
  taskManager.post_task({url : address});
  taskManager.post_task({url : address});
  taskManager.post_task({url : address});
  /*taskManager.post_task({url : address});
  taskManager.post_task({url : address});
  taskManager.post_task({url : address});
  taskManager.post_task({url : address});
  taskManager.post_task({url : address});
  taskManager.post_task({url : address});
  taskManager.post_task({url : address});
  taskManager.post_task({url : address});*/
}