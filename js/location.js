let map;
let markers = [];
const PRESET_KEYWORDS = ["咖啡", "早午餐", "日式", "韓食", "中式", "甜點", "牛排", "火鍋", "義大利麵", "素食"];

document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("food_input");
    const select = document.getElementById("food_select");
    if (!input) return;

    if (select) {
        PRESET_KEYWORDS.forEach((keyword) => {
            const option = document.createElement("option");
            option.value = keyword;
            option.textContent = keyword;
            select.appendChild(option);
        });

        select.addEventListener("change", () => {
            const selected = select.value;
            if (!selected) return;
            input.value = selected;
            handleKeywordSearch(selected);
        });
    }

    input.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();  // prevent form submission
            handleKeywordSearch(input.value);
        }
    });
});

function handleKeywordSearch(rawKeyword) {
    const keyword = rawKeyword.trim();
    if (!keyword) {
        alert("Please enter a food type.");
        MapVisible(false);
        return;
    }

    GeolocationCoordinates(keyword);
}

function GeolocationCoordinates(keyword) {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((pos) => 
            showPosOnMap(pos, keyword), showError);
    }
    else {
        alert("Geolocation is not supported by this browser.");
        MapVisible(false);
    }
}

/*
function showPosition(position) {
    alert("經度：" + position.coords.longitude +
    "\n緯度：" + position.coords.latitude);
}
*/

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

    MapVisible(false);
}

function clearMarker() {
    markers.forEach((m) => m.setMap(null));
    markers = [];
}

function showPosOnMap(pos, keyword) {
    const longitude = pos.coords.longitude;
    const latitude = pos.coords.latitude;
    const center = { lat: latitude, lng: longitude };

    const mapElement = document.getElementById("map");
    if (!mapElement) {
        alert("Map not found.");
        return;
    }

    // show the map
    MapVisible(true);

    map = new google.maps.Map(mapElement, {
        center: { lat: latitude, lng: longitude },
        zoom: 14.5
    });

    // clean markers before searching
    clearMarker();

    // user location
    const myMarker = new google.maps.Marker({
        position: center,
        map: map,
        title: "You are here"
    });
    markers.push(myMarker);

    // place api
    const service = new google.maps.places.PlacesService(map);
    const request = {
        location: center,
        radius: 1000,
        keyword: keyword,
        type: "restaurant"
    };

    service.nearbySearch(request, (results, status) => {
        if (status !== google.maps.places.PlacesServiceStatus.OK || !results) {
            alert("Place search failed, try other keyword.");
            MapVisible(false);
            return;
        }

        results.forEach((place) => {
            if (!place.geometry || !place.geometry.location) return;

            const marker = new google.maps.Marker({
                map: map,
                position: place.geometry.location,
                title: place.name
            });
            markers.push(marker);

            const info = new google.maps.InfoWindow({
                content: `
                    <div>
                        <strong>${place.name}</strong><br>
                        <strong>${"之後加餐廳資訊"}</strong><br>
                    </div>
                `
            });

            // 只要滑鼠碰到就開啟，移開就關掉
            marker.addListener("mouseover", () => {
                info.open(map, marker);
            });
            marker.addListener("mouseout", () => {
                info.close();
            });
        });
    });
}


// for map display
function MapVisible(isVisible) {
    const mapElement = document.getElementById("map");
    if (!mapElement) return;

    if (isVisible) {
        // show the map
        mapElement.classList.add("map-visible");
    }
    else {
        // hide the map
        mapElement.classList.remove("map-visible");
    }
}
