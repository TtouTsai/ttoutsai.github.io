function GeolocationCoordinates() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((pos) => {
            showPosition(pos);
            showPosOnMap(pos);
        }, showError);
    }
    else {
        alert("Geolocation is not supported by this browser.");
    }
}

function showPosition(position) {
    alert("經度：" + position.coords.longitude +
    "\n緯度：" + position.coords.latitude);
}

function showError(error) {
    switch(error.code) {
        case error.PERMISSION_DENIED:
            alert("User denied the request for Geolocation.");
            break;
        case error.POSITION_UNAVAILABLE:
            alert("Location information is unavailable.");
            break;
        case error.TIMEOUT:
            alert("The request to get user location timed out.");
            break;
        case error.UNKNOWN_ERROR:
            alert("An unknown error occurred.");
            break;
    }
}

// bug: no show
function showPosOnMap(pos) {
    const longitude = pos.coords.longitude;
    const latitude = pos.coords.latitude;

    const map = new google.maps.Map(document.getElementById("map"), {
        center: { lat: latitude, lng: longitude },
        zoom: 15
    });

    new google.maps.Marker({
        position: { lat: latitude, lng: longitude },
        map: map,
        title: "Your Location"
    });
}