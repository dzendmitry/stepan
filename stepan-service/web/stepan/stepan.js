(function () {

    var audioContext = null,
        gain_node = null,
        backgroupPage = chrome.extension.getBackgroundPage(),
        pc = null;

    // --- webrtc connectors

    function createPeerConnection() {
      var config = {
          sdpSemantics: 'unified-plan'
      };
  
      var pc = new RTCPeerConnection(config);
  
      return pc;
    }

    function negotiate() {
      return pc.createOffer().then(function(offer) {
        return pc.setLocalDescription(offer);
      }).then(function() {
        // wait for ICE gathering to complete
        return new Promise(function(resolve) {
            if (pc.iceGatheringState === 'complete') {
                resolve();
            } else {
                function checkState() {
                    if (pc.iceGatheringState === 'complete') {
                        pc.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                }
                pc.addEventListener('icegatheringstatechange', checkState);
            }
        });
      }).then(function() {
        var offer = pc.localDescription;
        var codec = "opus/48000/2";

        offer.sdp = sdpFilterCodec('audio', codec, offer.sdp);

        return fetch('http://127.0.0.1:8080/offer', {
            body: JSON.stringify({
                sdp: offer.sdp,
                type: offer.type,
            }),
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'POST'
        });
      }).then(function(response) {
        return response.json();
      }).then(function(answer) {
        return pc.setRemoteDescription(answer);
      }).catch(function(e) {
        alert(e);
      });
    }

    function sdpFilterCodec(kind, codec, realSdp) {
      var allowed = []
      var rtxRegex = new RegExp('a=fmtp:(\\d+) apt=(\\d+)\r$');
      var codecRegex = new RegExp('a=rtpmap:([0-9]+) ' + escapeRegExp(codec))
      var videoRegex = new RegExp('(m=' + kind + ' .*?)( ([0-9]+))*\\s*$')
      
      var lines = realSdp.split('\n');
  
      var isKind = false;
      for (var i = 0; i < lines.length; i++) {
          if (lines[i].startsWith('m=' + kind + ' ')) {
              isKind = true;
          } else if (lines[i].startsWith('m=')) {
              isKind = false;
          }
  
          if (isKind) {
              var match = lines[i].match(codecRegex);
              if (match) {
                  allowed.push(parseInt(match[1]));
              }
  
              match = lines[i].match(rtxRegex);
              if (match && allowed.includes(parseInt(match[2]))) {
                  allowed.push(parseInt(match[1]));
              }
          }
      }
  
      var skipRegex = 'a=(fmtp|rtcp-fb|rtpmap):([0-9]+)';
      var sdp = '';
  
      isKind = false;
      for (var i = 0; i < lines.length; i++) {
          if (lines[i].startsWith('m=' + kind + ' ')) {
              isKind = true;
          } else if (lines[i].startsWith('m=')) {
              isKind = false;
          }
  
          if (isKind) {
              var skipMatch = lines[i].match(skipRegex);
              if (skipMatch && !allowed.includes(parseInt(skipMatch[2]))) {
                  continue;
              } else if (lines[i].match(videoRegex)) {
                  sdp += lines[i].replace(videoRegex, '$1 ' + allowed.join(' ')) + '\n';
              } else {
                  sdp += lines[i] + '\n';
              }
          } else {
              sdp += lines[i] + '\n';
          }
      }
  
      return sdp;
    }

    function escapeRegExp(string) {
      return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); // $& means the whole matched string
    }

    // --- enable volume control for output speakers

    document.getElementById('volume').addEventListener('change', function() {

        var curr_volume = this.value;
        gain_node.gain.value = curr_volume;

        backgroupPage.console.log("curr_volume ", curr_volume);
    });

  document.getElementById('resume').addEventListener('click', function() {
      backgroupPage.console.log("audio is starting up ...");
      audioContext = new AudioContext();

      backgroupPage.console.log('sample rate: ', audioContext.sampleRate);
      
      if (!navigator.mediaDevices.getUserMedia) {
        backgroupPage.console.log('getUserMedia not supported on your browser!');
      }

      navigator.mediaDevices.getUserMedia({audio:true})
      .then(function(stream) {
        start_microphone(stream);
      })
      .catch(function(e) {
        alert('Error capturing audio.');
      });

      audioContext.resume().then(() => {
        backgroupPage.console.log("playback resumed successfully");
      });
    });

    document.getElementById('call').addEventListener('click', function() {
      pc = createPeerConnection();
      navigator.mediaDevices.getUserMedia({audio:true}).then(function(stream) {
            stream.getTracks().forEach(function(track) {
                pc.addTrack(track, stream);
            });
            return negotiate();
        }, function(err) {
            alert('Could not acquire media: ' + err);
        });
    });

  // ---

  function copy_data_to_output(event) {
    var inputBuffer = event.inputBuffer;
    var outputBuffer = event.outputBuffer;
    for (var channel = 0; channel < outputBuffer.numberOfChannels; channel++) {
      var inputData = inputBuffer.getChannelData(channel);
      var outputData = outputBuffer.getChannelData(channel);
      for (var sample = 0; sample < inputBuffer.length; sample++) {
        outputData[sample] = inputData[sample];
      }
    }
  }

  function process_microphone_buffer(event) { // invoked by event loop
    var microphone_output_buffer = event.inputBuffer.getChannelData(0); // just mono - 1 channel for now
    copy_data_to_output(event);
  }

  function start_microphone(stream) {

    gain_node = audioContext.createGain();
    gain_node.connect( audioContext.destination );

    var script_processor_node = audioContext.createScriptProcessor(0, 1, 1);
    script_processor_node.onaudioprocess = process_microphone_buffer;

    var microphone_stream = audioContext.createMediaStreamSource(stream);
    microphone_stream.connect(script_processor_node);
    script_processor_node.connect(gain_node);
  }

}());