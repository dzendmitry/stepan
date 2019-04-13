(function () {
    document.getElementById('call').addEventListener('click', function() {
      pc = createPeerConnection();
      dc = pc.createDataChannel('commands', {ordered: true});
      dc.onmessage = function(evt) {
          alert(evt.data);
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