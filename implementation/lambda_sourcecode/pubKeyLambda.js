const jsrsasign = require('jsrsasign');
const AWS = require('aws-sdk');

/*
*	Lambda function that should be called on registration of new Certificate on AWS IoT
*	AWS IoT rule triggers Lambda with argument certificateId.
*	This function grabs the X.509 PEM associated with Id and converts to a prime256v1 ECDSA Public Key in PEM format.
*	Public Key is then added to the Signature Verification Lambda function as an environment variable.
*/

exports.lambda_handler = function(event, context, callback) {
	// Grabbing Certificate in PEM format. Certificate is grabbed by certificateId, which is passed from AWS IoT rule upon certificate registration.
	var region = 'us-west-2';
	var iot = new AWS.Iot({'region': region, apiVersion: '2015-05-28'});
	var certificateId = event.certificateId.toString().trim();
	var params = {
		certificateId: certificateId
	};
	
	var zk_cert = '';
	iot.describeCertificate(params, function(err, data) {
		if (err) console.log(err, err.stack)
		else
		{	
			zk_cert = data['certificateDescription']['certificatePem'];
			// Grabbing Public key from Certificate PEM, public key then converted from hex_string to base64 encoded PEM format.
			var X509 = new jsrsasign.X509();
			X509.readCertPEM(zk_cert);
			var pub_key_hex = X509.getPublicKeyHex(zk_cert);
			//var pub_key_pem = '-----BEGIN PUBLIC KEY-----\n' +
			var pub_key_pem = Buffer.from(pub_key_hex, 'hex').toString('base64') + '\n';
			//'-----END PUBLIC KEY-----\n';
			
			// Public key PEM inserted into Environment Variables of Sig. Ver. lambda.
			var lambda = new AWS.Lambda();
			var params = {
				FunctionName: "iot_to_dynamo"
			};
			lambda.getFunction(params, function(err, data) {
				if (err) console.log(err, err.stack);
				else {	
					var new_environment = data['Configuration']['Environment'];
					if (new_environment == undefined)
					{
						new_environment = {};
						new_environment['Configuration'] = {};
						new_environment['Configuration']['Environment'] = {};
						new_environment['Configuration']['Environment']['Variables'] = {};
						new_environment = new_environment['Configuration']['Environment'];
					}
					new_environment['Variables']['new_pub_key'] = pub_key_hex;
					params = {
						FunctionName: "iot_to_dynamo",
						Environment: new_environment
					};	
					lambda.updateFunctionConfiguration(params, function(err, data){
						if (err) console.log(err, err.stack);
						else	console.log(data);
					});
				}
			})	;
		}
	});
}