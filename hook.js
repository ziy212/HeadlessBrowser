try {
  window['orgEval'] = window['eval'];
  window['eval'] = function(){
      for( var i=0; i < arguments.length; i++ )
      {
          console.log( "[REWRITE] EVAL:" + arguments[i] );
      }
      console.log("[HERE]");
      window['orgEval'].apply( window, arguments );
  }
}
catch (e) {
  console.log("[ERROR] [REWRITE] EVAL "+e);
}

try {
  window['orgFunction'] = window['Function'];
  window['Function'] = function(){
      for( var i=0; i < arguments.length; i++ )
      {
          console.log( "[REWRITE] FUNCTION:" + arguments[i] );
      }
      window['orgEval'].apply( window, arguments );
  }
}
catch (e) {
  console.log("[ERROR] [REWRITE] FUNCTION "+e);
}

try {
  window['orgSetTimeout'] = window['setTimeout'];
  window['setTimeout'] = function(){
      console.log( "[REWRITE] SETTIMEOUT:" + arguments[0] );
      window['orgSetTimeout'].apply( window, arguments );
  }
}
catch (e) {
  console.log("[ERROR] [REWRITE] SETTIMEOUT "+e);
}

try {
  window['orgSetInterval'] = window['setInterval'];
  window['setInterval'] = function(){
      console.log( "[REWRITE] SETINTERVAL:" + arguments[0] );
      window['orgSetInterval'].apply( window, arguments );
  }
}
catch (e) {
  console.log("[ERROR] [REWRITE] SETINTERVAL "+e);
}