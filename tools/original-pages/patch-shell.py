#!/usr/bin/env python3
"""Patch upstream Boxedwine's boxedwine-shell.js for GitHub Pages hosting.

GitHub Pages rejects files over 100 MB, but the Wine filesystem zip is ~150 MB.
The workflow splits it into <100 MB parts plus <name>.parts.json; this patch
makes loadFile() fall back to fetching and joining those parts when the whole
file is not found.
"""
import sys

path = sys.argv[1]
src = open(path, encoding="utf-8").read()

old = """      			} else {
      				console.log('Unable to load:' + filename + ' error:' + response.status);
      			}"""
new = """      			} else {
      				// Pages-hosted: large files are split into parts listed in <file>.parts.json
      				fetch(pathPrefix + filename + '.parts.json').then(function(r) {
      					if (r.status !== 200) { throw new Error('no parts manifest, status ' + r.status); }
      					return r.json();
      				}).then(function(parts) {
      					return Promise.all(parts.map(function(p) {
      						return fetch(pathPrefix + p).then(function(r) {
      							if (r.status !== 200) { throw new Error(p + ' status ' + r.status); }
      							return r.arrayBuffer();
      						});
      					}));
      				}).then(function(buffers) {
      					let total = buffers.reduce(function(n, b) { return n + b.byteLength; }, 0);
      					let arr = new Uint8Array(total);
      					let offset = 0;
      					buffers.forEach(function(b) { arr.set(new Uint8Array(b), offset); offset += b.byteLength; });
      					callback(arr);
      				}).catch(function(e) {
      					console.log('Unable to load:' + filename + ' error:' + response.status + ' / ' + e);
      				});
      			}"""
if src.count(old) != 1:
    sys.exit("patch-shell.py: loadFile() not found as expected; upstream changed")
open(path, "w", encoding="utf-8").write(src.replace(old, new))
print("patched", path)
