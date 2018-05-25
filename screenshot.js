"use strict";

// * Variables

var page = require('webpage').create(),
    system = require('system'),
    url, output_filename, size, pageWidth, pageHeight;

pageWidth = 1000;

// A shorter height would be nice, but with the enormous page headers
// nowadays (e.g. the stupid one inserted by GitHub unless you are
// logged in), you can't see anything!
pageHeight = 1000;

// ** Args

url = system.args[1];
output_filename = system.args[2];

// * Functions

function insert_css (stylesheet) {
    // Insert HTML STYLE element with contents of string STYLESHEET.

    var element = document.createElement('style');
    element.type = "text/css";
    element.innerHTML = stylesheet;

    document.getElementsByTagName("head")[0].appendChild(element);
}

function process_page (status) {
    if (status !== 'success') {
        console.log('Unable to load the address!');
        phantom.exit(1);
    }
    else {
        // Add stylesheet
        page.evaluate(insert_css, stylesheet);

        // Take screenshot
        window.setTimeout(
            function () {
                page.render(output_filename);
                phantom.exit();
            },
            200
        );
    }
}

// * Main

// Fix console output from page.evaluate()
page.onConsoleMessage = function (msg) {
    console.log("LOG: page.evaluate: " + msg);
};

// Log all external requests
// page.onResourceRequested = function (requestData, request) {
//     console.log('LOG: LOADING RESOURCE: ', requestData['url']);
// };

// ** Check args

page.viewportSize = {
    width: pageWidth,
    height: pageHeight
};
page.clipRect = {
    top: 0,
    left: 0,
    width: pageWidth,
    height: pageHeight
};

// ** Read CSS file from disk

var css_file = system.args[3];
var fs = require("fs");
var stylesheet = fs.read(css_file);

// ** Load and render page

page.open(url, process_page);
