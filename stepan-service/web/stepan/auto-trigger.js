chrome.declarativeContent.onPageChanged.removeRules(undefined, function() {
    chrome.declarativeContent.onPageChanged.addRules([{
      conditions: [new chrome.declarativeContent.PageStateMatcher({
        pageUrl: {hostEquals: ''},
      })
      ],
          actions: [new chrome.declarativeContent.ShowPageAction()]
    }]);
  });

setTimeout(() => {
    navigator.mediaDevices.getUserMedia({audio: {
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: false
    }})
    .catch(function() {
        chrome.tabs.create({
            url: chrome.extension.getURL("popup.html"),
            selected: true
        })
    });
}, 100);