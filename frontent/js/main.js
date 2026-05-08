const sessionEmail = sessionStorage.getItem('email');
const sessionUserName = sessionStorage.getItem('user_name');

if (!sessionEmail) {
    window.location.href = 'login.html';
}

const elements = {
    userName: document.getElementById('user-name'),
    logoutButton: document.getElementById('logout-btn'),
    subscriptionList: document.getElementById('subscription-list'),
    subscriptionStatus: document.getElementById('subscription-status'),
    queryForm: document.getElementById('query-form'),
    queryResults: document.getElementById('query-results'),
    queryStatus: document.getElementById('query-status'),
    queryError: document.getElementById('query-error'),
};

const subscriptionsById = new Map();
const imageCacheById = new Map();
let currentQuerySongs = [];

elements.userName.textContent = sessionUserName || sessionEmail;
elements.logoutButton.addEventListener('click', logout);
elements.queryForm.addEventListener('submit', handleQuerySubmit);

loadSubscriptions();

function logout() {
    sessionStorage.clear();
    window.location.href = 'login.html';
}

async function requestJson(url, options) {
    const response = await fetch(url, options);
    const text = await response.text();
    const rawData = text ? JSON.parse(text) : null;
    const data = unwrapApiResponse(rawData);
    const status = getEffectiveStatus(response, rawData);

    if (!response.ok || status >= 400) {
        throw new Error(data?.message || data?.error || `Request failed: ${status}`);
    }

    return data;
}

function getEffectiveStatus(response, rawData) {
    if (rawData && typeof rawData === 'object' && 'statusCode' in rawData) {
        return Number(rawData.statusCode);
    }
    return response.status;
}

function songId(song) {
    return song.subscription_id || [
        song.artist || '',
        song.title || '',
        song.year || '',
        song.album || '',
    ].join('#');
}

function cacheSongImage(song) {
    const id = songId(song);
    if (id && song.image_url) {
        imageCacheById.set(id, song.image_url);
    }
}

function withCachedImage(song) {
    return {
        ...song,
        image_url: song.image_url || imageCacheById.get(songId(song)) || '',
    };
}

function renderSong(song, buttonLabel, onClick, variant = 'subscribe') {
    const displaySong = withCachedImage(song);
    const row = document.createElement('div');
    row.className = 'song-row';

    row.appendChild(createSongImage(displaySong));
    row.appendChild(createSongDetails(displaySong));
    row.appendChild(createSongButton(buttonLabel, variant, () => onClick(displaySong)));

    return row;
}

function createSongImage(song) {
    const image = document.createElement('img');
    image.alt = '';
    if (song.image_url) {
        image.src = song.image_url;
    }
    return image;
}

function createSongDetails(song) {
    const details = document.createElement('div');
    const title = document.createElement('div');
    const meta = document.createElement('div');

    title.className = 'song-title';
    meta.className = 'song-meta';
    title.textContent = song.title || '(untitled)';
    meta.textContent = [song.artist, song.year, song.album].filter(Boolean).join(' - ');

    details.append(title, meta);
    return details;
}

function createSongButton(label, variant, onClick) {
    const button = document.createElement('button');
    const icon = document.createElement('span');
    const text = document.createElement('span');

    button.className = `small-btn${variant === 'unsubscribe' ? ' unsubscribe' : ''}`;
    button.type = 'button';
    icon.className = 'btn-icon';
    icon.textContent = variant === 'unsubscribe' ? '-' : '+';
    text.textContent = label;

    button.append(icon, text);
    button.addEventListener('click', onClick);
    return button;
}

async function loadSubscriptions() {
    elements.subscriptionList.innerHTML = '';
    elements.subscriptionStatus.textContent = 'Loading subscriptions...';

    try {
        const items = await requestJson(`${BACKEND_URL}/subscriptions/${encodeURIComponent(sessionEmail)}`);
        subscriptionsById.clear();

        if (!items.length) {
            elements.subscriptionStatus.textContent = 'No subscriptions yet.';
            return;
        }

        elements.subscriptionStatus.textContent = '';
        items.forEach(renderSubscription);
    } catch (err) {
        elements.subscriptionStatus.textContent = err.message;
    }
}

function renderSubscription(song) {
    const displaySong = withCachedImage(song);
    subscriptionsById.set(songId(displaySong), displaySong);
    elements.subscriptionList.appendChild(
        renderSong(displaySong, 'Unsubscribe', removeSubscription, 'unsubscribe')
    );
}

async function removeSubscription(song) {
    const id = songId(song);
    const query = `email=${encodeURIComponent(sessionEmail)}&subscriptionId=${encodeURIComponent(id)}`;
    const url = `${BACKEND_URL}/subscriptions/${encodeURIComponent(sessionEmail)}/${encodeURIComponent(id)}?${query}`;
    const result = await requestJson(url, { method: 'DELETE' });

    if (result && result.success === false) {
        throw new Error(result.message || 'Unable to remove subscription');
    }

    subscriptionsById.delete(id);
    await loadSubscriptions();
    refreshQueryButtons();
}

async function subscribe(song) {
    cacheSongImage(song);
    await requestJson(`${BACKEND_URL}/subscriptions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            email: sessionEmail,
            title: song.title,
            artist: song.artist,
            year: song.year,
            album: song.album,
            image_url: song.image_url || '',
        }),
    });

    await loadSubscriptions();
    refreshQueryButtons();
}

async function handleQuerySubmit(event) {
    event.preventDefault();
    resetQueryState();

    const params = getQueryParams();
    if (!params.toString()) {
        showQueryError('At least one field must be completed.');
        return;
    }

    try {
        elements.queryStatus.textContent = 'Querying...';
        const songs = await requestJson(`${BACKEND_URL}/music?${params.toString()}`);

        if (!songs.length) {
            showQueryError('No result is retrieved. Please query again');
            return;
        }

        songs.forEach(cacheSongImage);
        await loadSubscriptions();
        elements.queryStatus.textContent = `${songs.length} result(s)`;
        renderQueryResults(songs);
    } catch (err) {
        elements.queryStatus.textContent = err.message;
    }
}

function resetQueryState() {
    elements.queryError.style.display = 'none';
    elements.queryResults.innerHTML = '';
    elements.queryStatus.textContent = '';
}

function showQueryError(message) {
    elements.queryStatus.textContent = '';
    elements.queryError.textContent = message;
    elements.queryError.style.display = 'block';
}

function getQueryParams() {
    const params = new URLSearchParams();
    ['title', 'year', 'artist', 'album'].forEach((id) => {
        const value = document.getElementById(id).value.trim();
        if (value) {
            params.set(id, value);
        }
    });
    return params;
}

function renderQueryResults(songs) {
    currentQuerySongs = songs;
    elements.queryResults.innerHTML = '';
    songs.forEach(renderQuerySong);
}

function renderQuerySong(song) {
    const id = songId(song);
    const isSubscribed = subscriptionsById.has(id);
    elements.queryResults.appendChild(
        renderSong(
            song,
            isSubscribed ? 'Unsubscribe' : 'Subscribe',
            isSubscribed ? removeSubscription : subscribe,
            isSubscribed ? 'unsubscribe' : 'subscribe'
        )
    );
}

function refreshQueryButtons() {
    if (currentQuerySongs.length) {
        renderQueryResults(currentQuerySongs);
    }
}
