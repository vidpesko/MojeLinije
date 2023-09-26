const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

submitBtn = document.getElementById('get-routes-btn');
navigationFormContainer = document.getElementById('navigation-form-container');
navigationForm = document.getElementById('navigation-form');

closePathsBtn = document.getElementById('close-paths');
clearSearchBtn = document.getElementById('clear-search');
sourceInput = document.getElementById('source-input');
destInput = document.getElementById('dest-input');

exploreModal = document.getElementById('explore-container');


function togglePathSearch() {
    navigationFormContainer.classList.add('executed-search');
    navigationForm.classList.add('executed-search-form');
    document.getElementById('possible-paths').hidden = false;
    closePathsBtn.hidden = false;
}

submitBtn.onclick = function () {
    togglePathSearch();
    handleFormSearch();
}

closePathsBtn.onclick = function () {
    navigationFormContainer.classList.remove('executed-search');
    navigationForm.classList.remove('executed-search-form');
    document.getElementById('possible-paths').hidden = true;
    closePathsBtn.hidden = true;
}

function showClearSearchBtn() {
    if (sourceInput.value.length == 0 && destInput.value.length == 0) {
        clearSearchBtn.hidden = true;
    } else {
        clearSearchBtn.hidden = false;
    }
}

clearSearchBtn.onclick = function () {
    sourceInput.value = '';
    destInput.value = '';
    clearSearchBtn.hidden = true;
}

function toggleExploreModal() {
    if (exploreModal.hidden == true) {
        exploreModal.hidden = false;
    } else {
        exploreModal.hidden = true;
    }
}

function checkForSearchUrl() {
    const searchByUrl = '{{ search_by_url }}';
    if (searchByUrl == 'True') {
        togglePathSearch();
        sendRouteSearch('{{ source }}', '{{ dest }}', '{{ source_type }}', '{{ dest_type }}');
    }
}

function addPossiblePath(name, transfers, dep_t, arr_t) {
    var htmlCode = `<div class="possible-path row w-100 p-0 m-0 text-center">
        <h6>${name}</h6>
        <div class="col">
            <p>${dep_t}<br><i class="bi bi-arrow-down-short"></i><br>${arr_t}</p>
            </div>
                <div class="col">
                    <p><i class="bi bi-arrow-left-right"></i></p>
                    <p>${transfers}</p>
                </div>
                <div class="col">
                    <p>Vrsta vozil:</p>
                    <i class="bi bi-bus-front-fill"></i>, <i class="bi bi-train-front-fill"></i>
                </div>
                <button id="first-path-name" onclick="focusOnPath('${name}')">Explore</button>
        </div>`

    const pathDiv = document.createElement("div");
    pathDiv.innerHTML = htmlCode;
    var divContainer = document.getElementById('paths-container');
    divContainer.appendChild(pathDiv);
}

function getInputType(input) {
    // Convert val to int if it is number
    var value = +input;
    rType = 'int';
    // If it is not a number
    if (isNaN(value) == true) {
        value = input;
        rType = 'str';
    }
    return { 'type': rType, 'value': value }
}

function inputValidation(val, errorFunc, htmlEl) {
    var isError = false;
    var rType;
    var msg = '';
    var value;

    if (val == '') {
        msg = 'empty';
        isError = true;
    } else if (val.trim() == '') {
        msg = 'Kaksna praznina';
        isError = true;
    }

    val = getInputType(val);

    if (isError == true) {
        errorFunc(msg, htmlEl);
    }
    return { 'error': isError, 'type': val['type'], 'value': val['value'] }
}

function modifyUrl(newUrl) {
    window.history.pushState("", "", newUrl);
}

function inCaseOfInputError(errorText, htmlEl) {
    htmlEl.innerHTML = errorText;
    htmlEl.hidden = false;
}

function handleFormSearch() {
    sourceErrorDisplay = document.getElementById('source-error-display');
    destErrorDisplay = document.getElementById('dest-error-display');
    var sourceValidation = inputValidation(sourceInput.value, inCaseOfInputError, sourceErrorDisplay);
    var destValidation = inputValidation(destInput.value, inCaseOfInputError, destErrorDisplay);

    if (sourceValidation['error'] == true || destValidation['error'] == true) {
        console.log('very bad')
        return
    }

    // Change url to reflect search
    var newUrl = `/?source=${sourceValidation['value']}&source_type=${sourceValidation['type']}&dest=${destValidation['value']}&dest_type=${destValidation['type']}`;
    modifyUrl(newUrl);
    sendRouteSearch(sourceValidation['value'], destValidation['value'], sourceValidation['type'], destValidation['type']);
}


// Center map to include all stops from all possible paths
function centerMapOnPaths(stops, map) {
    var bound = new google.maps.LatLngBounds();
    for (var i = 0; i < stops.length; i++) {
        bound.extend(stops);
    }
    map.fitBounds(bound, 50);
}


// Loader
var spinner = document.getElementById('spinner');
var toHide = document.getElementsByClassName('to-hide-spinner');

function startLoader() {
    for (var i = 0; i < toHide.length; i++) {
        toHide[i].classList.add('style-for-spinner');
    }
    spinner.hidden = false;
}

function stopLoader() {
    spinner.hidden = true;
    for (var i = 0; i < toHide.length; i++) {
        toHide[i].hidden = false;
    }
}


// Google Maps section
var firstStation = { 'id': 0 };
var allMarkers = {};
var clusterfick = {};
var loadedStations = false;
var foundRoutes = {};
var map;
var pathCoordinates = {};
var formattedCoordinates = {};
var formattingCoordsDone = false;

// All used icons
const ICON_LINKS = {
    'bus_station_min': '{% static "map_assets/icons/bus_station_min.png" %}',
    'train_station_min': '{% static "map_assets/icons/train_station_min.png" %}',
    'bus_station': '{% static "map_assets/icons/bus_station.png" %}',
    'bus_station_start': '{% static "map_assets/icons/bus_station_start.png" %}',
    'bus_station_finish': '{% static "map_assets/icons/bus_station_finish.png" %}',
    'bus_station_hidden': '{% static "map_assets/icons/bus_station_hidden.png" %}'
}

// var firstBtn = document.getElementById('first-path')


const SLO_BORDER_STYLE = {
    'strokeColor': 'blue',
    'strokeWeight': 2,
}

const OTHER_COUNTRY_STYLE = {
    'strokeColor': '#000055',
    'strokeWeight': 1,
    'fillColor': '#000000',
    'fillOpacity': 0.6
}

const MUNICIPALITY_STYLE = {
    'strokeColor': 'red',
    'strokeWeight': 2,
    // 'fillColor': '#00ff00',
    'fillOpacity': 0.6
}

const SLO_BOUNDS = {
    north: 46.95,
    south: 45.4,
    west: 13.296389,
    east: 16.701944,
}


function changeClusterfickMarkers(cl) {
    for (var i = 0; i < cl.markers_.length; i++) {
        cl.markers_[i].setIcon(ICON_LINKS['bus_station_hidden']);
        // cl.markers_[i].setVisible(false);
    }
}

function showClusterfick(cl) {
    cl.markers_ = cl.myHiddenMarkers;
}

function hideClusterfick(cl) {
    cl.myHiddenMarkers = cl.markers_;
    cl.markers_ = [];
}

function createCenterControl(map, where) {
    const controlButton = document.getElementById("recenter-btn");

    controlButton.addEventListener("click", () => {
        map.setCenter(where);
        map.setZoom(9);
        showClusterfick(clusterfick['cluster']);
    });
    return controlButton;
}

function addMarkerInfo(marker, name, id, vehicleType, infoWindow, map) {
    marker.addListener("mouseover", () => {
        infoWindow.setContent(
            '<div id="content">' +
            '<div id="siteNotice">' +
            "</div>" +
            `<h1 id="firstHeading" class="firstHeading">${name} - ${id}</h1>` +
            '<div id="bodyContent">' +
            `<p>${vehicleType}</p>` +
            "</div>" +
            "</div>"
        );
        infoWindow.open({
            anchor: marker,
            map,
        });
    });

    marker.addListener("mouseout", () => {
        infoWindow.close();
        document.getElementById("source-input").focus();
        // document.getElementById("source-input").blur();
    });

}

function loadStations(map) {
    const infoWindow = new google.maps.InfoWindow({
        content: '',
        ariaLabel: "Station",
    });
    map.data.loadGeoJson('{% static "map_assets/GeoJson/ijpp_stations.json" %}', null, function (features) {
        var i = 0;
        var markers = features.map(function (feature) {
            var g = feature.getGeometry();
            var vehicleType = feature.getProperty('bus_train');
            var name = feature.getProperty('stop_name');
            var id = feature.getProperty('stop_id')

            if (vehicleType == 'bus') {
                var marker = new google.maps.Marker({ 'position': g.get(), 'data': feature, 'icon': ICON_LINKS['bus_station_min'], 'clickable': true });
                allMarkers[id] = marker;

                // Select a station
                marker.addListener("click", () => {
                    console.log(marker)
                    // If one station is already selected - choosing the second one
                    if (firstStation['id'] != 0) {
                        marker.setIcon('https://developers.google.com/maps/documentation/javascript/examples/full/images/beachflag.png');
                        // ENOUGH DATA - execute search
                        console.log(firstStation['id'])
                        console.log(id)
                        // sendStations(firstStation['id'], id);

                    } else {
                        marker.setIcon('https://w7.pngwing.com/pngs/722/1011/png-transparent-logo-icon-instagram-logo-instagram-logo-purple-violet-text-thumbnail.png');
                        firstStation['id'] = id;
                    }
                });
            } else {
                var marker = new google.maps.Marker({ 'position': g.get(), 'data': feature, 'icon': ICON_LINKS['train_station_min'] });
            }
            addMarkerInfo(marker, name, id, vehicleType, infoWindow, map);

            i++;
            if (i == features.length) {
                loadedStations = true;
            }

            return marker;
        });

        // var markerCluster = new markerClusterer.MarkerClusterer(map, markers);
        // const imagePath = "https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m";
        const imagePath = "{% static 'map_assets/cluster_icons' %}/m";
        var clusterStyles = [
            {
                textColor: 'white',
                url: "{% static 'map_assets/cluster_icons/c1.png' %}",
                height: 50,
                width: 50
            },
            {
                textColor: 'white',
                url: "{% static 'map_assets/cluster_icons/c2.png' %}",
                height: 90,
                width: 90
            },
            {
                textColor: 'white',
                url: "{% static 'map_assets/cluster_icons/m3.png' %}",
                height: 66,
                width: 65
            }
        ];
        const markerClusterer = new MarkerClusterer(map, markers, { imagePath: imagePath, gridSize: 100, maxZoom: 14, ignoreHiddenMarkers: true, styles: clusterStyles });
        clusterfick['cluster'] = markerClusterer;
        // return markers
    });
    map.data.setStyle({ visible: false });
}

function hideMarkers(markers) {
    for (let i = 0; i < markers.length; i++) {
        markers[i].setMap(null);
    }
}

async function myMap() {
    const sloCenter = new google.maps.LatLng(46.119944, 14.815333);
    var mapProp = {
        center: sloCenter,
        // restriction: {
        //     latLngBounds: SLO_BOUNDS,
        //     strictBounds: false,
        // },
        zoom: 9,
        // disableDefaultUI: true,
        mapId: '223555717bccec41',
        clickableIcons: false,
        gestureHandling: 'greedy',
    };
    map = new google.maps.Map(document.getElementById("map"), mapProp);

    // ? Drawing a border around SLO
    const countryLayer = map.getFeatureLayer(google.maps.FeatureType.COUNTRY);
    countryLayer.style = (options) => {
        if (options.feature.placeId == 'ChIJYYOWXuckZUcRZdTiJR5FQOc') {
            return SLO_BORDER_STYLE
        } else {
            return OTHER_COUNTRY_STYLE
        }
    }


    // Code for regions of Slovenia
    var bounds = {}
    map.data.loadGeoJson('{% static "map_assets/GeoJson/regije_slo.geojson" %}', null, function (features) {

        var regions = features.map(function (feature) {
            var bound = new google.maps.LatLngBounds();
            var g = feature.getGeometry();
            g.forEachLatLng(function (e) {
                bound.extend(e);

            });
            var region_name = feature.getProperty('SR_UIME');
            bounds[region_name] = bound;
        });
    });
    map.data.setStyle({
        strokeColor: 'green',
        strokeWeight: 2,
        fillOpacity: 0
    });
    map.data.addListener('click', (e) => {
        map.fitBounds(bounds[e.feature.getProperty('SR_UIME')]);
        loadStations(map);
    });


    // Button to center map
    const centerControlDiv = document.getElementById('custom-map-controls');
    const centerControl = createCenterControl(map, sloCenter);
    map.controls[google.maps.ControlPosition.TOP_CENTER].push(centerControlDiv);

    // firstBtn.onclick = function () {sendStations(1121307, 1122692, map); }
    checkForSearchUrl();
}

const every_nth = (arr, nth) => arr.filter((e, i) => i % nth === nth - 1);



function getRawCoordinates(coords) {
    var newCoords = [];
    for (var i = 0; i < coords.length; i++) {
        // console.log(coords[i])
        var pathCoords = [];
        for (var n = 0; n < coords[i].length; n++) {
            // newCoords.push({ 'lat': coords[i][n]['lat'], 'lng': coords[i][n]['lng'] });
            pathCoords.push([coords[i][n]['lat'], coords[i][n]['lng']]);
        }
        // console.log(pathCoordinates)
        if (pathCoords.length != 0) {
            newCoords.push(pathCoords);
        }
    }
    // newCoords = every_nth(newCoords, 5)
    return newCoords
}

function formatCoordinatesToLatLng(coords) {
    var newCoords = []
    coords = coords.snappedPoints;
    for (var n = 0; n < coords.length; n++) {
        var coord = coords[n].location;
        newCoords.push({ 'lat': coord.latitude, 'lng': coord.longitude });

        // newCoords.push({'lat': coords[n][0], 'lng': coords[n][1] });
    }
    return newCoords
}

function snapCoordinatesToRoads(coords, path_name) {
    var isLastPath = false;

    for (var n = 0; n < coords.length; n++) {
        if ((n + 1) == coords.length) {
            isLastPath = true;
        }
        var connectionCoords = coords[n];
        snapPathCoordinates(connectionCoords, path_name, n, isLstPath = isLastPath);
    }
}

function snapPathCoordinates(pathCoords, path_name, indexOfPath, isLastPath = false) {
    var chunkSize = 95;
    var _firstStation = 0;
    var isLast = false;

    for (var i = 0; i < pathCoords.length; i += chunkSize) {
        if (i == 0) {
            _firstStation = pathCoords[0];
        }
        if ((isLastPath == true) && ((i + chunkSize) >= pathCoords.length)) {
            isLast = true;
        }
        // if (((i + chunkSize) >= connectionCoords.length) && (n + 1 == coords.length)) {
        // isLast = true;
        // }
        snapToRoadsCall(pathCoords.slice(i, i + chunkSize), path_name, indexOfPath, _firstStation = _firstStation, isLast = isLast);
    }
}

async function snapToRoadsCall(coords, path_name, indexOfPath, _firstStation = 0, isLast = false) {
    // ! First coord (which is coord of station) should be excluded/remained intact from snap to roads algo
    var path = coords.join('|');
    $.get('https://roads.googleapis.com/v1/snapToRoads', {
        interpolate: true,
        key: '{{ GOOGLE_MAPS_API_KEY }}',
        path: path
    }, function (data) {
        data = formatCoordinatesToLatLng(data);

        // Add previously stored station coord
        if (_firstStation != 0) {
            var station = { lat: _firstStation[0], lng: _firstStation[1] }
            data.splice(0, 0, station);
        }

        // Adding newly received data to coordinate array
        // formattedCoordinates[path_name] = formattedCoordinates[path_name].concat(data);
        // formattedCoordinates[path_name].splice(indexOfPath, 0, ...data);
        formattedCoordinates[path_name][indexOfPath] = data;

        if (isLast == true) {
            // console.log('here')
            formattingCoordsDone = true;
        }
    });
    // response = response.text();
}

function fillArrayWithPlaceholders(path_name, coordinates) {
    for (var n = 0; n < coordinates.length; n++) {
        formattedCoordinates[path_name].push([]);
    }
}

function unpack2dArray(array) {
    var newArr = []
    for (var n = 0; n < array.length; n++) {
        newArr.push(...array[n]);
    }
    return newArr
}

function prepareCoordinatesForPath(path_name) {
    var coordinates = pathCoordinates[path_name];
    formattedCoordinates[path_name] = [];
    coordinates = getRawCoordinates(coordinates);
    fillArrayWithPlaceholders(path_name, coordinates);

    // formattedCoordinates[path_name] = formatCoordinatesToLatLng(coordinates[2]);
    // formattedCoordinates[path_name].concat(formatCoordinatesToLatLng(coordinates[1]))
    // formattingCoordsDone = true;
    // return
    snapCoordinatesToRoads(coordinates, path_name);
    // if (formattingCoordsDone == true) {
    // console.log('gehehhe')
    // formattedCoordinates[path_name] = formatCoordinatesToLatLng(formattedCoordinates[path_name]);
    // }
}

// var intervalID = window.setInterval(function d() {console.log(formattingCoordsDone); console.log(loadedStations)}, 500);

function focusOnPath(path_name, trying = false) {
    var bound = new google.maps.LatLngBounds();
    var stops = foundRoutes[path_name];
    // Place first marker
    if ((loadedStations == false) && (trying == false) && (formattingCoordsDone == true)) {
        loadStations(map);
        focusOnPath(path_name, trying = true);
    } else if (((trying == true) || (formattingCoordsDone == false)) && (loadedStations == false)) {
        setTimeout(function () {
            focusOnPath(path_name, true);
        }, 50);
    }

    // hideMarkers(allMarkers);

    stop_id = stops[0]['stop_id'];
    marker = allMarkers[stop_id];
    // if (marker === undefined) {
    //     focusOnPath(path_name, trying = false)
    // }
    var coordinates = formattedCoordinates[path_name];
    coordinates = unpack2dArray(coordinates);

    // First marker
    marker.setIcon(ICON_LINKS['bus_station_start']);
    clusterfick['cluster'].removeMarker(marker);
    marker.setMap(map);

    var lastMarkerPos = {};

    bound.extend(marker.position);
    for (var i = 1; i < stops.length; i++) {
        station = stops[i];
        isTransferStop = station['transfer'];
        stop_id = stops[i]['stop_id'];
        marker = allMarkers[stop_id];
        if (isTransferStop == true) {
            marker.setIcon('https://developers.google.com/maps/documentation/javascript/examples/full/images/beachflag.png');
        }
        if (i == (stops.length - 1)) {
            marker.setIcon(ICON_LINKS['bus_station_finish']);
            lastMarkerPos = { 'lat': marker.getPosition().lat(), 'lng': marker.getPosition().lng() };
            coordinates.push(lastMarkerPos);
        }
        clusterfick['cluster'].removeMarker(marker);
        marker.setMap(map);

        bound.extend(marker.position);
    }

    // for (var i = 0; i < .length; i++) {
    // coordinates.push(marker.position);
    hideClusterfick(clusterfick['cluster']);
    // hideClusterfick(clusterfick['cluster']);
    // drawMarkers(coordinates);
    drawPath(coordinates);
    map.fitBounds(bound, 50);
}

function drawMarkers(coordinates) {
    console.log(coordinates)
    const infoWindow = new google.maps.InfoWindow({
        content: '',
        ariaLabel: "path",
    });
    for (var i = 0; i < coordinates.length; i++) {
        var c = coordinates[i];
        // c = {'lat': c[0], 'lng': c[1]}
        // console.log(c)
        var marker = new google.maps.Marker({ 'position': c });
        marker.setMap(map);
        addMarkerInfo(marker, i, i, i, infoWindow, map)
    }
}

function drawPath(coordinates) {
    const outerPath = new google.maps.Polyline({
        path: coordinates,
        geodesic: true,
        strokeColor: "#FFFFFF",
        strokeOpacity: 1.0,
        strokeWeight: 7,
    });

    const innerPath = new google.maps.Polyline({
        path: coordinates,
        geodesic: true,
        strokeColor: "#0C6FFD",
        strokeOpacity: 1.0,
        strokeWeight: 4,
    });

    // Trying to display info on line
    innerPath.addListener("mouseover", () => {
        console.log("heeyah");
    });
    innerPath.setMap(map);
    outerPath.setMap(map);
}

// Sending source/dest to server
function sendRouteSearch(station_1, station_2, s_type, d_type) {
    startLoader();
    $.ajax({
        type: 'GET',
        url: `/api/path/?source=${station_1}&destination=${station_2}&source_type=${s_type}&dest_type=${d_type}&format=json`,
        success: function (response) {
            stopLoader();
            // console.log(Object.keys(response.routes))
            var routes = response.routes;
            for (var i = 0; i < routes.length; i++) {
                route = routes[i];
                r_name = route['name']
                transfers = route['transfers'];
                dep_t = route['departure_time'];
                arr_t = route['arrival_time'];
                foundRoutes[r_name] = route['stops'];
                pathCoordinates[r_name] = [];
                // for (var n = 0; n < Object.keys(route['connections']).length; n++) {
                //     console.log(con)
                // }
                for (const [key, value] of Object.entries(route['connections'])) {
                    var con = value['coordinates'];
                    pathCoordinates[r_name].push(con);
                }
                prepareCoordinatesForPath(r_name);
                addPossiblePath(r_name, transfers, dep_t, arr_t);
            }
        },
        error: function (error) { console.log(error) }
    });
}
