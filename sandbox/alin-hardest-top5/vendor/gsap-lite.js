/* Minimal GSAP-compatible timeline used for offline HyperFrames rendering. */
(function () {
  function toArray(target) {
    if (typeof target === "string") return Array.from(document.querySelectorAll(target));
    if (!target) return [];
    if (target instanceof Element) return [target];
    return Array.from(target);
  }

  function cleanProps(props) {
    var out = {};
    Object.keys(props || {}).forEach(function (key) {
      if (key === "duration" || key === "ease" || key === "stagger" || key === "overwrite") return;
      out[key] = props[key];
    });
    return out;
  }

  function num(value, fallback) {
    var n = Number(value);
    return Number.isFinite(n) ? n : fallback;
  }

  function applyState(el, state) {
    var x = num(state.x, 0);
    var y = num(state.y, 0);
    if (x || y) el.style.transform = "translate(" + x + "px, " + y + "px)";
    else el.style.transform = "";
    if (state.opacity !== undefined) el.style.opacity = String(state.opacity);
  }

  function interpolate(from, to, progress) {
    var state = {};
    ["x", "y", "opacity"].forEach(function (key) {
      if (from[key] === undefined && to[key] === undefined) return;
      var a = num(from[key], key === "opacity" ? 1 : 0);
      var b = num(to[key], key === "opacity" ? 1 : 0);
      state[key] = a + (b - a) * Math.max(0, Math.min(1, progress));
    });
    return state;
  }

  function Timeline() {
    this._tweens = [];
    this._time = 0;
    this._paused = true;
  }

  Timeline.prototype._add = function (kind, target, props, position) {
    var duration = num(props && props.duration, 0);
    var stagger = num(props && props.stagger, 0);
    var start = num(position, 0);
    var clean = cleanProps(props);
    var elements = toArray(target);
    for (var i = 0; i < elements.length; i += 1) {
      var from = {};
      var to = {};
      if (kind === "from") {
        from = clean;
        to = {};
      } else if (kind === "to") {
        from = {};
        to = clean;
      } else {
        to = clean;
      }
      this._tweens.push({
        kind: kind,
        element: elements[i],
        start: start + i * stagger,
        duration: duration,
        from: from,
        to: to,
      });
    }
    return this;
  };

  Timeline.prototype.from = function (target, props, position) {
    return this._add("from", target, props, position);
  };

  Timeline.prototype.to = function (target, props, position) {
    return this._add("to", target, props, position);
  };

  Timeline.prototype.set = function (target, props, position) {
    return this._add("set", target, props, position);
  };

  Timeline.prototype.fromTo = function (target, fromProps, toProps, position) {
    var props = Object.assign({}, toProps || {});
    var duration = num(props.duration, 0);
    var stagger = num(props.stagger, 0);
    var start = num(position, 0);
    var elements = toArray(target);
    for (var i = 0; i < elements.length; i += 1) {
      this._tweens.push({
        kind: "fromTo",
        element: elements[i],
        start: start + i * stagger,
        duration: duration,
        from: cleanProps(fromProps || {}),
        to: cleanProps(toProps || {}),
      });
    }
    return this;
  };

  Timeline.prototype.seek = function (time) {
    this._time = num(time, 0);
    var touched = new Set();
    this._tweens.forEach(function (tween) {
      touched.add(tween.element);
    });
    touched.forEach(function (el) {
      applyState(el, { x: 0, y: 0, opacity: 1 });
    });
    var now = this._time;
    this._tweens
      .slice()
      .sort(function (a, b) {
        return a.start - b.start;
      })
      .forEach(function (tween) {
        var end = tween.start + tween.duration;
        if (tween.kind === "set") {
          if (now >= tween.start) applyState(tween.element, tween.to);
          return;
        }
        if (now < tween.start) {
          if (tween.kind === "from" || tween.kind === "fromTo") applyState(tween.element, tween.from);
          return;
        }
        if (now >= end) {
          applyState(tween.element, tween.to);
          return;
        }
        var progress = tween.duration > 0 ? (now - tween.start) / tween.duration : 1;
        applyState(tween.element, interpolate(tween.from, tween.to, progress));
      });
    return this;
  };

  Timeline.prototype.totalTime = function (time) {
    return this.seek(time);
  };

  Timeline.prototype.time = function () {
    return this._time;
  };

  Timeline.prototype.duration = function () {
    return this.totalDuration();
  };

  Timeline.prototype.totalDuration = function () {
    return this._tweens.reduce(function (max, tween) {
      return Math.max(max, tween.start + tween.duration);
    }, 0);
  };

  Timeline.prototype.pause = function () {
    this._paused = true;
    return this;
  };

  Timeline.prototype.paused = function () {
    return this._paused;
  };

  Timeline.prototype.kill = function () {
    this._tweens = [];
  };

  Timeline.prototype.eventCallback = function () {
    return this;
  };

  window.gsap = {
    version: "offline-lite",
    timeline: function () {
      return new Timeline();
    },
    set: function (target, props) {
      toArray(target).forEach(function (el) {
        if (props && props.clearProps) {
          el.style.transform = "";
          el.style.opacity = "";
        } else {
          applyState(el, cleanProps(props || {}));
        }
      });
    },
    registerPlugin: function () {},
  };
})();
