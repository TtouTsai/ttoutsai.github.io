let map;
let markers = [];
let placeIndex = {};           // place_id -> { marker, info }
let activeInfoWindow = null;   // keep only one open at a time
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
    placeIndex = {};
    if (activeInfoWindow) {
        activeInfoWindow.close();
        activeInfoWindow = null;
    }
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

            const infoContent = `
                <div>
                    <strong>${place.name}</strong><br>
                    ${place.vicinity ? `<span>${place.vicinity}</span><br>` : ""}
                </div>
            `;
            const marker = new google.maps.Marker({
                map: map,
                position: place.geometry.location,
                title: place.name
            });
            markers.push(marker);

            const info = new google.maps.InfoWindow({ content: infoContent });
            placeIndex[place.place_id] = { marker, info };

            // 只要滑鼠碰到就開啟，移開就關掉
            marker.addListener("mouseover", () => {
                info.open(map, marker);
            });
            marker.addListener("mouseout", () => {
                info.close();
            });
        });

        // -------- ② 組成 {name, place_id} 陣列給後端 --------
        const targetShops = results
            .filter((p) => p.place_id)
            .map((p) => ({
                name: p.name || "",
                place_id: p.place_id
            }));
        console.log("找到的目標店家:", targetShops);

        // -------- ③ 傳到後端 --------
        fetch("http://localhost:8000/api/process_places", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ target_shops: targetShops })
        })
        .then((res) => res.json())
        .then((data) => {
            console.log("後端 ML 回傳:", data);
            showTop5Results(data.top5);
        })
        .catch((err) => console.error("後端連接錯誤:", err));
    });

}

// -------- ④ 顯示後端回傳的最佳五家 --------
function showTop5Results(top5) {
    const list = document.getElementById("top5_list");
    if (!list) return;

    list.innerHTML = "";

    top5.forEach((item, idx) => {
        const displayScore = typeof item.score === "number" ? item.score.toFixed(2) : item.score;
        const li = document.createElement("li");
        li.textContent = `${idx + 1}. ${item.name} (score: ${displayScore})`;
        li.style.cursor = "pointer";
        li.title = "點擊以聚焦地圖";
        li.addEventListener("click", () => focusPlace(item.place_id, item));
        list.appendChild(li);
    });
}

function focusPlace(placeId, item) {
    if (!map) return;
    const record = placeIndex[placeId];
    if (!record || !record.marker) {
        alert("找不到這個地點的地圖標記，請重新搜尋。");
        return;
    }

    const position = record.marker.getPosition();
    if (position) {
        map.panTo(position);
        map.setZoom(16);
    }

    // 更新資訊窗內容並開啟
    if (activeInfoWindow) {
        activeInfoWindow.close();
    }

    const scoreText = typeof item?.score === "number" ? `Score: ${item.score.toFixed(2)}` : "";
    const infoHtml = `
        <div>
            <strong>${item?.name || record.marker.getTitle() || "Restaurant"}</strong><br>
            ${scoreText}
        </div>
    `;
    record.info.setContent(infoHtml);
    record.info.open(map, record.marker);
    activeInfoWindow = record.info;
}
