(function () {
    function openLink(href) {
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            var tab = tabs[0];
            chrome.tabs.update(tab.id, {url: href});
        });
    }
    document.getElementById('call').addEventListener('click', function() {
      pc = createPeerConnection();
      dc = pc.createDataChannel('commands', {ordered: true});
      dc.onmessage = function(evt) {
          switch(evt.data) {
              case 'Commands.STATE_SKIPPED':
              chrome.browserAction.setIcon({path: 'images/circle_red_48x48.png'});
              break;
              case 'Commands.STEPAN':
              chrome.browserAction.setIcon({path: 'images/circle_green_48x48.png'});
              break;
              case 'Commands.SHOW_CATALOG_API':
              break;
              case 'Commands.SHOW_K8S_API':
              break;
              case 'Commands.SHOW_ITEM_API':
              break;
          }
        };
      navigator.mediaDevices.getUserMedia({audio:true}).then(function(stream) {
            stream.getTracks().forEach(function(track) {
                pc.addTrack(track, stream);
            });
            return negotiate(pc);
        }, function(err) {
            alert('Could not acquire media: ' + err);
        });
    });
}());