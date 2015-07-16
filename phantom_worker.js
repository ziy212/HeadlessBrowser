var queue = require('./Queue'),
  system = require('system'),
  taskWorker,
  /* parameters */
  address, times, index,
  /* settings */
  defaultUserAgent, userAgent, defaultTimeout, timeout,
  /* utilities */
  waitForTaskFinish, displayObject;

/* Settings */
defaultUserAgent = 
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:38.0) Gecko/20100101 Firefox/38.0";
defaultTimeout = 5000;

function b64EncodeUnicode(str) {
    return btoa(encodeURIComponent(str).replace(/%([0-9A-F]{2})/g, function(match, p1) {
        return String.fromCharCode('0x' + p1);
    }));
}

/* Task Worker */
taskWorker = (function (){
  var user_agent, timeout, current_url,
    task_queue = new queue(), page = null,
    fin_task_count = 0, err_task_count = 0,
    error_tag = false,
    configure, post_task, start_tasks, 
    open_url, open_url_callback,
    get_remaining_task_count, get_fin_task_count, get_error_tag;

  configure = function(settings) {
    user_agent = settings.user_agent;
    timeout = settings.timeout;
  };

  post_task = function (task) {
    task_queue.enqueue(task);
    console.log("[ADD_TASK] adding a browsing task: " + 
      task_queue.getLength());
  };

  open_url_callback = function (result) {
    try{
      if (result.status !== 'success') {
        console.log('[FAIL] to load the address:'+result.url);
      }
      else {
        console.log("[SUCCEED] to load the address: " + result.url +
        ", contnet-size: "+result.content.length,
        ", failed objects: "+ result.failed_obj_count,
        ", landing-page: "+result.landing_page);
        //console.log(result.content);
        send_contents(current_url, result.content, result.landing_page)
      }
    }
    catch (err) {
      console.log("[PHANTOM_ERR] error in open_url_callback "+err);
    }
    finally { 
      //fin_task_count++;   
      if (task_queue.getLength() > 0) {
        //make sure the page is null!
        console.log("[INFO] Start next task, "+task_queue.getLength()+" left");
        start_tasks();
      }
    }
  };

  send_contents = function (url, contents, landing_url) {
    var db_listener = "http://localhost:4040/api/web-contents/contents-store",
      sender, error = null, 
      json_header, encoded_contents, data;
    sender = require('webpage').create();
    sender.settings.resourceTimeout = 5000;
    sender.settings.userAgent = user_agent; 

    sender.onResourceTimeout = function (e) {
      error = "timeout";
    };

    console.log("[INFO] sending contents to DB: "+contents.length);
    encoded_contents = b64EncodeUnicode(contents);
    data = '{"url":"' + encodeURIComponent(url) +
          '","landing_url":"' + encodeURIComponent(landing_url) +
          '","contents":"'+encoded_contents+'"}';
    console.log("[DEBUG] "+encoded_contents.length);
    json_header = { "Content-Type": "application/json" };
    try{
      sender.open(db_listener, 'post', data, json_header,
       function (status) {
        //page.render('github.png');
        content = page.content.slice(0);
        sender.close();
        sender = null;
        
        if (status !== 'success'){
          err_task_count++;
          console.log("[FAIL] failed to send contents to DB; failed cases "+err_task_count);
        }
        else if (error) {
          err_task_count++;
          console.log("[FAIL] failed to send contents to DB; failed cases "+err_task_count);
        }
        console.log("[SUCCEED] sent contents ["+contents.length+"] to db");
        //
      });
    }
    catch (err) {
      console.log("[PHANTOM_ERR] error sending contents to db "+err);
      sender.close();
      page = null;
      error_tag = true;
    }
    finally {
      fin_task_count++;
    } 
  };

  //this method creates and closes the page instance
  open_url = function (url) {
    var landing_page = url, content, timeout_count = 0,
      request_count = 0, response_count = 0;
    if (page !== null) {
      console.log("[ERROR] last instance hasn't finished!!!");
      return ;
    }
    page = require('webpage').create();
    page.settings.resourceTimeout = 5000;
    page.settings.userAgent = user_agent;
    
    page.onResourceRequested = function (req) {
      //console.log("request:"+req.url);
      request_count++;
    };

    page.onResourceReceived = function (res) {
      response_count++;
      //if (res.redirectURL) {
      //    landing_page = res.redirectURL;
      //}
    };

    page.onResourceTimeout = function (e) {
      timeout_count++;
    };

    console.log("[INFO] start browsing: "+url);
    try{
      console.log("[DEBUG] start browsing: "+url);
      page.open(url, function (status) {
        //page.render('github.png');
        console.log("[DEBUG] done opening: "+url+" "+status);
        content = page.content.slice(0);
        if (status === "success"){
          //console.log("PAGE:"+page);
          landing_page = page.url.slice(0);
        }    
        page.close();
        page = null;
        
        open_url_callback({
          status : status,
          url : url,
          landing_page : landing_page,
          request_count : request_count,
          response_count : response_count,
          failed_obj_count : timeout_count,
          content : content
        });
      });
    }
    catch (err) {
      console.log("[PHANTOM_ERR] error in open "+url+" error:"+err);
      page.close();
      page = null;
      error_tag = true;
    }
    finally { } 
  };

  start_tasks = function () {
    var task;
    if (task_queue.getLength()>0 && page === null) {
        task = task_queue.dequeue();
        current_url = task.url;
        open_url(task.url);
    }
    else {
      console.log("[INFO] can NOT start task: "+
        task_queue.getLength()+" "+page);
    }
  };

  get_remaining_task_count = function () {
    return task_queue.getLength();
  };

  get_fin_task_count = function() {
    return fin_task_count;
  };

  get_error_tag = function () {
    return error_tag;
  }

  return {
    configure : configure,
    post_task : post_task,
    start_tasks : start_tasks,
    get_remaining_task_count : get_remaining_task_count,
    get_fin_task_count : get_fin_task_count,
    get_error_tag : get_error_tag
  };

})();

/* Utilities */
displayObject = function (obj) {
  var item;
  for (item in obj) {
    if (obj.hasOwnProperty(item)) {
        console.log("KEY: "+ item+" VAL:"+obj[item]);
    }
  }
};

waitForTaskFinish = function(count) {
  if (!taskWorker.get_error_tag() &&
    taskWorker.get_fin_task_count() < count) {
    console.log("[MAIN] finished ["+taskWorker.get_fin_task_count() +
      "/"+count+"] tasks, check 2s later");
    setTimeout(function(){waitForTaskFinish(count)},
      2000);
  }
  else {
    console.log("[MAIN] having finished "+
      taskWorker.get_fin_task_count()+" tasks");
    phantom.exit();
  }
};

/* main */
if (system.args.length < 3) {
  console.log(
    "usage: phantom-worker.js url times timeout-for-one-req userAgent");
}
else {
  address = system.args[1];
  times = parseInt(system.args[2]);
  if (system.args.length >3 ){
    timeout = parseInt(system.args[3]);
  }
  else {
    timeout = defaultTimeout;
  }
  if (system.args.length > 4){
    userAgent = system.args[4];
  }
  else {
    userAgent = defaultTimeout;
  }
  console.log("[MAIN] browsing "+address+" for "+times);
  taskWorker.configure({
    timeout : timeout,
    user_agent : userAgent });
  index = 0;
  while (index++ < times) {
    taskWorker.post_task({url : address});
  }
  taskWorker.start_tasks();
  waitForTaskFinish(times);
}


