// To access by a browser in another computer, use the external IP of machine running AttackMapServer
// from the same computer(only), you can use the internal IP.
// Example:
// - AttackMapServer machine:
//   - Internal IP: 127.0.0.1
//   - External IP: 192.168.11.106
var webSock = new WebSocket("ws:/127.0.0.1:8888/websocket"); // Internal
//var webSock = new WebSocket("ws:/192.168.1.100:8888/websocket"); // External

// link map
L.mapbox.accessToken = "pk.eyJ1IjoibW1heTYwMSIsImEiOiJjaWgyYWU3NWQweWx2d3ltMDl4eGk5eWY1In0.9YoOkALPP7zaoim34ZITxw";


class TrafficMap {
    constructor (mapname) {

        this.name = mapname;
        this.map = L.mapbox.map("map", "mapbox.dark", {
            center: [0, 0], // lat, long
            zoom: 2
        });

        // add full screen option
        L.control.fullscreen().addTo(this.map);

        // hq coords
        this.hqLatLng = new L.LatLng(37.3845, -122.0881);

        // hq marker
        L.circle(this.hqLatLng, 110000, {
            color: 'red',
            fillColor: 'yellow',
            fillOpacity: 0.5,
        }).addTo(this.map);

        // Append <svg> to map
        this.svg = d3.select(this.map.getPanes().overlayPane).append("svg")
            .attr("class", "leaflet-zoom-animated")
            .attr("width", window.innerWidth)
            .attr("height", window.innerHeight);

        // Append <g> to svg
        //var g = svg.append("g").attr("class", "leaflet-zoom-hide");
        // Re-draw on reset, this keeps the markers where they should be on reset/zoom
        this.map.on("moveend", this.update);


        this.circles = new L.LayerGroup();
        this.map.addLayer(this.circles);
    }

    sayname () {
        return this.name
    }

    LayerPoint (LatLng) {
        return this.map.latLngToLayerPoint(LatLng)
    }

    translateSVG () {
        const viewBoxLeft = document.querySelector("svg.leaflet-zoom-animated").viewBox.animVal.x;
        const viewBoxTop = document.querySelector("svg.leaflet-zoom-animated").viewBox.animVal.y;

        // Resizing width and height in case of window resize
        this.svg.attr("width", window.innerWidth);
        this.svg.attr("height", window.innerHeight);

        // Adding the ViewBox attribute to our SVG to contain it
        this.svg.attr("viewBox", function () {
            return "" + viewBoxLeft + " " + viewBoxTop + " " + window.innerWidth + " " + window.innerHeight;
        });

        // Adding the style attribute to our SVG to translate it
        this.svg.attr("style", function () {
            return "transform: translate3d(" + viewBoxLeft + "px, " + viewBoxTop + "px, 0px);";
        })
    }

    update () {
        this.translateSVG();
        // additional stuff
    }


    static calcMidpoint (x1, y1, x2, y2, bend) {
        if (y2 < y1 && x2 < x1) {
            let tmpy = y2;
            let tmpx = x2;
            x2 = x1;
            y2 = y1;
            x1 = tmpx;
            y1 = tmpy;
        } else if (y2 < y1) {
            y1 = y2 + (y2 = y1, 0);
        } else if (x2 < x1) {
            x1 = x2 + (x2 = x1, 0);
        }

        const radian = Math.atan(-((y2 - y1) / (x2 - x1)));
        const r = Math.sqrt(x2 - x1) + Math.sqrt(y2 - y1);
        const m1 = (x1 + x2) / 2;
        const m2 = (y1 + y2) / 2;

        const min = 2.5, max = 7.5;
        //var min = 1, max = 7;
        const arcIntensity = parseFloat((Math.random() * (max - min) + min).toFixed(2));

        let a, b;
        if (bend === true) {
            a = Math.floor(m1 - r * arcIntensity * Math.sin(radian));
            b = Math.floor(m2 - r * arcIntensity * Math.cos(radian));
        } else {
            a = Math.floor(m1 + r * arcIntensity * Math.sin(radian));
            b = Math.floor(m2 + r * arcIntensity * Math.cos(radian));
        }

        return {"x": a, "y": b};
    }

    translateAlong (path) {
        const l = path.getTotalLength();
        return function (i) {
            return function (t) {
                // Put in try/catch because sometimes floating point is stupid..
                try {
                    const p = path.getPointAtLength(t * l);
                    return "translate(" + p.x + "," + p.y + ")";
                } catch (err) {
                    console.log("Caught exception.");
                    return "ERROR";
                }
            }
        }
    }

    handleParticle (msg, srcPoint) {
        // var i = 0;
        const x = srcPoint['x'];
        const y = srcPoint['y'];

        this.svg.append('circle')
            .attr('cx', x)
            .attr('cy', y)
            .attr('r', 1e-6)
            .style('fill', 'none')
            //.style('stroke', d3.hsl((i = (i + 1) % 360), 1, .5))
            .style('stroke', msg.color)
            .style('stroke-opacity', 1)
            .transition()
            .duration(2000)
            .ease(Math.sqrt)
            .attr('r', 35)
            .style('stroke-opacity', 1e-6)
            .remove();

        //d3.event.preventDefault();
    }

    handleTraffic (msg, srcPoint, dstPoint) {
        const fromX = srcPoint['x'];
        const fromY = srcPoint['y'];
        let toX = dstPoint['x'];
        let toY = dstPoint['y'];
        const bendArray = [true, false];
        const bend = bendArray[Math.floor(Math.random() * bendArray.length)];
        // console.log(fromX)
        // console.log(fromY)
        // console.log(toX)
        // console.log(toY)
        if (fromX === toX && fromY === toY) {
            toX = toX + 1;
            toY = toY + 1;
            console.log("slide 1 point")
        }

        const lineData = [srcPoint, TrafficMap.calcMidpoint(fromX, fromY, toX, toY, bend), dstPoint];
        const lineFunction = d3.svg.line()
            .interpolate("basis")
            .x(function (d) {
                return d.x;
            })
            .y(function (d) {
                return d.y;
            });

        const lineGraph = this.svg.append('path')
            .attr('d', lineFunction(lineData))
            .attr('opacity', 0.8)
            .attr('stroke', msg.color)
            .attr('stroke-width', 2)
            .attr('fill', 'none');

        if (this.translateAlong(lineGraph.node()) === 'ERROR') {
            console.log('translateAlong ERROR');
            return;
        }

        const circleRadius = 6;

        // Circle follows the line
        const dot = this.svg.append('circle')
            .attr('r', circleRadius)
            .attr('fill', msg.color)
            .transition()
            .duration(700)
            .ease('ease-in')
            .attrTween('transform', this.translateAlong(lineGraph.node()))
            .each('end', function () {
                d3.select(this)
                    .transition()
                    .duration(500)
                    .attr('r', circleRadius * 2.5)
                    .style('opacity', 0)
                    .remove();
            });

        const length = lineGraph.node().getTotalLength();
        lineGraph.attr('stroke-dasharray', length + ' ' + length)
            .attr('stroke-dashoffset', length)
            .transition()
            .duration(700)
            .ease('ease-in')
            .attr('stroke-dashoffset', 0)
            .each('end', function () {
                d3.select(this)
                    .transition()
                    .duration(100)
                    .style('opacity', 0)
                    .remove();
            });
    }

    addCircle (msg, srcLatLng, dstLatLng) {
        const circleCount = this.circles.getLayers().length;
        const circleArray = this.circles.getLayers();

        // Only allow 50 circles to be on the map at a time
        if (circleCount >= 50) {
            this.circles.removeLayer(circleArray[0]);
        }
        L.circle(srcLatLng, 50000, {
            color: msg.color,
            fillColor: msg.color,
            fillOpacity: 0.2,
        }).addTo(this.circles);

        if (circleCount >= 50) {
            this.circles.removeLayer(circleArray[0]);
        }
        L.circle(dstLatLng, 50000, {
            color: msg.color,
            fillColor: msg.color,
            fillOpacity: 0.2,
        }).addTo(this.circles);
    }

    static prependAttackRow (id, args) {
        let tr = document.createElement('tr');
        const count = args.length;

        for (let i = 0; i < count; i++) {
            let td = document.createElement('td');
            if (args[i] === args[2]) {
                let path = 'flags/' + args[i] + '.png';
                let img = document.createElement('img');
                img.src = path;
                td.appendChild(img);
                tr.appendChild(td);
            } else {
                let textNode = document.createTextNode(args[i]);
                td.appendChild(textNode);
                tr.appendChild(td);
            }
        }

        let element = document.getElementById(id);
        const rowCount = element.rows.length;

        // Only allow 50 rows
        if (rowCount >= 50) {
            element.deleteRow(rowCount - 1);
        }

        element.insertBefore(tr, element.firstChild);
    }

    static prependTypeRow (id, args) {
        let tr = document.createElement('tr');
        const count = args.length;

        for (let i = 0; i < count; i++) {
            let td = document.createElement('td');
            let textNode = document.createTextNode(args[i]);
            td.appendChild(textNode);
            tr.appendChild(td);
        }

        let element = document.getElementById(id);
        const rowCount = element.rows.length;

        // Only allow 50 rows
        if (rowCount >= 50) {
            element.deleteRow(rowCount - 1);
        }

        element.insertBefore(tr, element.firstChild);
    }

    static prependCVERow (id, args) {
        let tr = document.createElement('tr');

        //count = args.length;
        const count = 1;

        for (let i = 0; i < count; i++) {
            let td1 = document.createElement('td');
            // var td2 = document.createElement('td');
            let td3 = document.createElement('td');
            let td4 = document.createElement('td');
            let td5 = document.createElement('td');
            let td6 = document.createElement('td');

            // Timestamp
            let textNode2 = document.createTextNode(args[0]);
            td1.appendChild(textNode2);
            tr.appendChild(td1);

            // Exploit

            //var textNode = document.createTextNode(args[1]);

            //var alink = document.createElement('a');
            //alink.setAttribute("href", args[1]);
            //alink.setAttribute("target", "_blank")
            //alink.style.color = "white";
            //alink.appendChild(textNode);

            //td2.appendChild(alink);
            //tr.appendChild(td2);

            // Flag
            let path = 'flags/' + args[2] + '.png';
            let img = document.createElement('img');
            img.src = path;
            td3.appendChild(img);
            tr.appendChild(td3);

            // IP
            let textNode3 = document.createTextNode(args[3]);
            td4.appendChild(textNode3);
            tr.appendChild(td4);

            // dst Flag
            let dst_path = 'flags/' + args[4] + '.png';
            let dst_img = document.createElement('img');
            dst_img.src = dst_path;
            td5.appendChild(dst_img);
            tr.appendChild(td5);

            // dst IP
            let textNode4 = document.createTextNode(args[5]);
            td6.appendChild(textNode4);
            tr.appendChild(td6);
        }

        const element = document.getElementById(id);
        const rowCount = element.rows.length;

        // Only allow 50 rows
        if (rowCount >= 50) {
            element.deleteRow(rowCount - 1);
        }

        element.insertBefore(tr, element.firstChild);
    }

    redrawCountIP (hashID, id, countList, codeDict) {
        $(hashID).empty();
        const element = document.getElementById(id);

        // Sort ips greatest to least
        // Create items array from dict
        let items = Object.keys(countList[0]).map(function (key) {
            return [key, countList[0][key]];
        });
        // Sort the array based on the second element
        items.sort(function (first, second) {
            return second[1] - first[1];
        });
        // Create new array with only the first 50 items
        const sortedItems = items.slice(0, 50);
        const itemsLength = sortedItems.length;

        for (let i = 0; i < itemsLength; i++) {
            let tr = document.createElement('tr');
            let td1 = document.createElement('td');
            let td2 = document.createElement('td');
            let td3 = document.createElement('td');
            let key = sortedItems[i][0];
            let value = sortedItems[i][1];
            let keyNode = document.createTextNode(key);
            let valueNode = document.createTextNode(value);
            let path = 'flags/' + codeDict[key] + '.png';
            let img = document.createElement('img');
            img.src = path;
            td1.appendChild(valueNode);
            td2.appendChild(img);

            let alink = document.createElement('a');
            alink.setAttribute("href", "#");
            alink.setAttribute("class", "showInfo");
            alink.style.color = "white";
            alink.appendChild(keyNode);

            td3.appendChild(alink);
            tr.appendChild(td1);
            tr.appendChild(td2);
            tr.appendChild(td3);
            element.appendChild(tr);
        }
    }

    redrawCountIP2 (hashID, id, countList, codeDict) {
        $(hashID).empty();
        const element = document.getElementById(id);

        // Sort ips greatest to least
        // Create items array from dict
        let items = Object.keys(countList[0]).map(function (key) {
            return [key, countList[0][key]];
        });
        // Sort the array based on the second element
        items.sort(function (first, second) {
            return second[1] - first[1];
        });
        // Create new array with only the first 50 items
        const sortedItems = items.slice(0, 50);
        const itemsLength = sortedItems.length;

        for (let i = 0; i < itemsLength; i++) {
            let tr = document.createElement('tr');
            let td1 = document.createElement('td');
            let td2 = document.createElement('td');
            let td3 = document.createElement('td');
            let key = sortedItems[i][0];
            let value = sortedItems[i][1];
            let keyNode = document.createTextNode(key);
            let valueNode = document.createTextNode(value);
            let path = 'flags/' + codeDict[key] + '.png';
            let img = document.createElement('img');
            img.src = path;
            td1.appendChild(valueNode);
            td2.appendChild(img);

            td3.appendChild(keyNode);
            tr.appendChild(td1);
            tr.appendChild(td2);
            tr.appendChild(td3);
            element.appendChild(tr);
        }
    }

    handleLegend (msg) {
        const ipCountList = [msg.src_ips_tracked, msg.src_iso_code];
        const countryCountList = [msg.src_countries_tracked, msg.src_iso_code];
        const attackList = [msg.event_time, msg.src_ip, msg.src_iso_code, msg.src_country, msg.src_city, msg.protocol];
        this.redrawCountIP('#ip-tracking', 'ip-tracking', ipCountList, msg.ip_to_code);
        this.redrawCountIP2('#country-tracking', 'country-tracking', countryCountList, msg.country_to_code);
        TrafficMap.prependAttackRow('attack-tracking', attackList);
    }

    static handleLegendType (msg) {
        const attackType = [msg.msg_type2];
        const attackCve = [msg.event_time, msg.msg_type3, msg.src_iso_code, msg.src_ip, msg.dst_iso_code, msg.dst_ip,
            //msg.country,
            //msg.city,
            //msg.protocol
        ];

        if (attackType != "___") {
            TrafficMap.prependTypeRow('attack-type', attackType);
        }

        if (attackCve[1] != "___") {
            TrafficMap.prependCVERow('attack-cveresp', attackCve);
        }
    }

}

// WEBSOCKET STUFF
const map_obj = new TrafficMap("Traffic");
console.log("mapobj init fin.");
console.log(map_obj.sayname())

webSock.onmessage = function (e) {
    console.log("Got a websocket message...");
    try {
        var msg = JSON.parse(e.data);
        console.log(msg);
        switch (msg.msg_type) {
            case "Traffic":
                var srcLatLng = new L.LatLng(msg.src_latitude, msg.src_longitude);
                var dstLatLng = new L.LatLng(msg.dst_latitude, msg.dst_longitude);
                // console.log(srcLatLng);
                // console.log(dstLatLng);

                // var hqPoint = map.latLngToLayerPoint(hqLatLng);
                var dstPoint = map_obj.LayerPoint(dstLatLng);
                var srcPoint = map_obj.LayerPoint(srcLatLng);
                map_obj.addCircle(msg, srcLatLng, dstLatLng);
                map_obj.handleParticle(msg, srcPoint);
                map_obj.handleTraffic(msg, srcPoint, dstPoint, srcLatLng);
                map_obj.handleLegend(msg);
                TrafficMap.handleLegendType(msg)
                break;
            // Add support for other message types?
        }
    } catch (err) {
        console.log(err)
    }
};

$(document).on("click", "#informIP #exit", function (e) {
    $("#informIP").hide();
});

$(document).on("click", '.container-fluid .showInfo', function (e) {
    var iplink = $(this).text();
    $("#informIP").show();
    $("#informIP").html(
        "<a id='ip_only' href='" + iplink + "'></a>" +
        "<button id='exit'>X</button><h3>" + iplink + "</h3><br>" +
        "<ul>" +
        "<li><a target= '_blank' href='http://www.senderbase.org/lookup/?search_string=" + iplink + "'><b><u color=white>Senderbase</a></li>" +
        "<li><a target='_blank' href='https://ers.trendmicro.com/reputations/index'>Trend Micro</a></li>" +
        "<li><a target='_blank' href='http://www.anti-abuse.org/multi-rbl-check-results/?host=" + iplink + "'>Anti-abuse</a></li>" +
        "</ul><br>" +
        "<button id='blockIP' alt='" + iplink + "'>Block IP</button>");
});


$(document).on("click", "#informIP #blockIP", function (e) {
    var ip = $(this).attr('alt');
    var ipBlocked = "ip_blocked:" + ip;
    console.log("Sending message: " + ipBlocked);
    webSock.send(ipBlocked);
});
