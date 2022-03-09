var http = require("http");
setInterval(function() {
    http.get("https://momentum-bot-sd.herokuapp.com");
}, 300000); // every 5 minutes (300000)