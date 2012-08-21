/* Nimble v0.4 helper library */

/* Protocol processors */

function NimbleSimple(word_limiter, phrase_limiter) {
    this.id = 1;

    this.word_limiter = ' ';//typeof word_limiter=='object'?' ':word_limiter;
    this.phrase_limiter = '\n';//typeof phrase_limiter==='object'?'\n':phrase_limiter;

    this.validate_arguments = function(args) {
        for(i=0; i<args.length; i=i+1) {
            if(args[i].search(this.word_limiter)>0 || args[i].search(this.phrase_limiter)>0)
                throw 'Nimble protocol error: Simple protocol uses space and \ n char as limiter';
        }
    };

    this.dump = function(command, args) {
        args.splice(0, 0, command);
        return args.join(this.word_limiter);
    };

    this.load = function(text) {
        var lines = text.split(this.phrase_limiter);
        var is_error = lines[0]=='ERROR';
        var data = lines.slice(1);
        var results = [];

        //TODO: protocol "feature"
        if(data.length == 1) {
            results = data[0].split(this.word_limiter)
            if(results.length == 1)
                results = data[0];
        }
        else {
            for(i=0; i<data.length; i++)
                results.push(data[i].split(this.word_limiter));
        }

        return {is_error: is_error, results : results};
    };
}

function NimbleJSON() {
    this.id = 2;

    this.validate_arguments = function(args) {
    };

    this.dump = function(command, args) {
        return JSON.stringify({command: command,
                args   : args});
    }

    this.load = function(text) {
        var obj = JSON.parse(text);
        return obj;
    };
}

/*
    Main class

    Usage example:
    var need_json = False;
    if(need_json)
        conn = new NimbleConnection('http://server/', new NimbleJSON());
    else
        conn = new NimbleConnection('http://server/');
    myajaxframework.request(conn.get_url(),
                            {method: POST,
                             postBody: conn.make_request('get_from_server', ['object', 2]),
                             onResponse: function(resp){var res = conn.parse_response(resp.text);}
                            }
    );
*/

function NimbleConnection(url, protocol) {
    this.server = url;
    this.protocol = typeof protocol === 'object'?protocol:new NimbleSimple();

    this.get_url = function() {
        return this.server+'/p:'+this.protocol.id+'/';
    };

    this.make_request = function(command, params) {
        this.protocol.validate_arguments(params);
        return this.protocol.dump(command, params);
    };

    this.parse_response = function(text) {
        var obj = this.protocol.load(text);
        if(obj.is_error)
            throw obj.results;
        return obj.results;
    };

    this.request_by_jquery = function(command, params, onsuccess, onerror) {
	    var make_response_func = function(context) {
	      return function(text) {
          try {
            resp = context.parse_response(text);
            onsuccess(resp);
          }
          catch(error) {
            onerror(error);
          }
	    };
	};

	$.ajax({type: "POST",
	        url: this.get_url(),
	        data: this.make_request(command,params),
	        dataType: 'text'
	}).done(make_response_func(this));
    };
}
