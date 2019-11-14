(function() {
    'use strict';
    /*
    @CommentService
    */
    angular
        .module('CustomerApp')

    .factory('CustomerService', [
        '$http', '$window',
        function($http, $window) {

            console.log("Hello!")

            var version = "678";

            // This is also not a good way to do this anymore.
            var sStorage = $window.sessionStorage;

            var customer_service_base_url = "http://127.0.0.1:5000/api"
            if(window.location.href.indexOf("localhost") > -1) {
                customer_service_base_url = "http://127.0.0.1:5000/api";
            } else if (window.location.href.indexOf("s3") > -1) {
                var customer_service_base_url = "http://flask-env.cgs7gmmhbm.us-east-2.elasticbeanstalk.com/api";
            }

            return {
                get_version: function () {
                    return ("1234");
                },
                driveLogin: function (email, pw) {

                    return new Promise(function(resolve, reject) {
                        console.log("Driving login.")
                        var url = customer_service_base_url + "/login";
                        console.log("email = " + email);
                        console.log("PW = " + pw);

                        var bd = {"email": email, "password": pw};
                        console.log(bd);
                        $http.post(url, bd).then(
                            function (data) {
                                console.log(data)
                                var result = data.data[0]
                                var headers = data.headers
                                var h = headers();
                                console.log("Data = " + JSON.stringify(result, null, 4));
                                console.log("Headers = " + JSON.stringify(h, null, 4))

                                var auth = h.authorization;
                                sStorage.setItem("token", auth);
                                resolve("OK")
                            },
                            function (error) {
                                console.log("Error = " + JSON.stringify(error, null, 4));
                                reject("Error")
                            }
                        );
                    });
                },
                getCustomer: function (email) {

                    return new Promise(function(resolve, reject) {
                        var token = sStorage.getItem("token");
                        if (token == null){
                            alert("Please log in first");
                            reject("Not login");
                        } else {
                            console.log("token= "+token);
                            var url = customer_service_base_url + "/user/" + email;
                            var header = {
                                headers: {'Authorization': token}
                            }
                            console.log(header)
                            $http.get(url, header).then(
                                function (data) {
                                    var json_data = data;

                                    json_data["data"] = {
                                        "id": data["data"]["id"],
                                        "email": data["data"]["email"],
                                        "last_name": data["data"]["last_name"],
                                        "first_name": data["data"]["first_name"],
                                        "status": data["data"]["status"]
                                     };
                                    var rsp = json_data;
                                    console.log("RSP = " + JSON.stringify(rsp, null, 4));
                                    resolve(rsp.data);
                                },
                                function (error) {
                                    console.log("Error = " + JSON.stringify(error, null, 4));
                                    reject("Error");
                                }
                            );
                        }
                    })
                },
                createCustomer: function (user_info) {
                    return new Promise(function(resolve, reject) {
                        var url = customer_service_base_url + "/registration";
                        
                        $http.post(url, user_info).then(
                            function (data) {
                                var result = data.data;
                                console.log("Data = " + JSON.stringify(result, null, 4));
                                resolve(result)
                            },
                            function (error) {
                                console.log("Error = " + JSON.stringify(error, null, 4));
                                reject("Error")
                            }
                        );
                    })
                },
            }
        }
    ])
})();