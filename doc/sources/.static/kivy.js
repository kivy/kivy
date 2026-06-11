document.addEventListener("DOMContentLoaded", function() {

    // Simple native cookie helper functions to replace $.cookie
    function getCookie(name) {
        let value = "; " + document.cookie;
        let parts = value.split("; " + name + "=");
        if (parts.length === 2) return parts.pop().split(";").shift();
        return null;
    }

    function setCookie(name, value) {
        document.cookie = name + "=" + value + "; path=/; max-age=31536000";
    }

    var bodyshortcut = false;
    function ensure_bodyshortcut() {
        if (bodyshortcut === true) return;
        
        var firstH1 = document.querySelector('div.body h1');
        if (firstH1) {
            firstH1.insertAdjacentHTML('afterend', '<div class="bodyshortcut">&nbsp;</div>');
            bodyshortcut = true;
        }
    }

    // If it's an API page, show the module name
    var pagename = location.pathname.split('/');
    var is_api = false;
    pagename = pagename[pagename.length - 1];
    
    if (pagename.search('api-') === 0) {
        pagename = pagename.substring(4, pagename.length - 5); // Refactored calculation matching standard .html stripping

        ensure_bodyshortcut();
        var shortcutDiv = document.querySelector('div.bodyshortcut');
        if (shortcutDiv) {
            shortcutDiv.insertAdjacentHTML('beforeend', '<div class="left">Module: <a href="#">' + pagename + '</a></div>');
        }
        is_api = true;
    }

    // Insert breaker only for the first data/class/function found
    var apibreaker = false;
    var apiElements = document.querySelectorAll('div.body dl[class]');
    
    apiElements.forEach(function(elem) {
        var hasValidClass = elem.classList.contains('data') || 
                            elem.classList.contains('class') || 
                            elem.classList.contains('exception') || 
                            elem.classList.contains('function');
                            
        if (!hasValidClass) return;
        
        // Don't accept dl inside dl
        if (elem.closest('dl') && elem.parentElement.closest('dl')) return;

        elem.classList.add('api-level');

        if (apibreaker === true) return;
        
        elem.insertAdjacentHTML('beforebegin', 
            '<div id="api"><h2>API <a id="api-toggle-desc" class="showed">Hide Description &uArr;</a></h2></div>'
        );
        apibreaker = true;
    });

    // Hover styling on dt elements
    document.querySelectorAll('div.body dl[class] dt').forEach(function(dt) {
        dt.addEventListener('mouseenter', function() { this.classList.add('hover'); });
        dt.addEventListener('mouseleave', function() { this.classList.remove('hover'); });
    });

    if (apibreaker === true) {
        ensure_bodyshortcut();
        var shortcutDiv = document.querySelector('div.bodyshortcut');
        if (shortcutDiv) {
            shortcutDiv.insertAdjacentHTML('beforebegin', '<div class="navlink right"><a id="api-link" href="#api">Jump to API</a> &dArr;</div>');
        }
    }

    // Event listener logic for Description toggle
    var toggleDescBtn = document.getElementById('api-toggle-desc');
    if (toggleDescBtn) {
        toggleDescBtn.addEventListener('click', function() {
            var targetElements = document.querySelectorAll('div.body dl.api-level > dd p, div.body dl.api-level > dd pre, div.body dl.api-level > dd blockquote, div.body dl.api-level > dd ul');
            
            if (this.classList.contains('showed')) {
                targetElements.forEach(el => el.style.display = 'none');
                this.classList.remove('showed');
                this.innerHTML = 'Show Descriptions &dArr;';
                setCookie('kivy.toggledesc', 'true');
            } else {
                targetElements.forEach(el => el.style.display = '');
                this.classList.add('showed');
                this.innerHTML = 'Hide Descriptions &uArr;';
                setCookie('kivy.toggledesc', 'false');
            }
        });
    }

    // Accordion toggle on specific definitions click
    document.querySelectorAll('div.body dl.api-level dt').forEach(function(dt) {
        dt.addEventListener('click', function() {
            var nextSibling = this.nextElementSibling;
            if (nextSibling) {
                Array.from(nextSibling.children).forEach(function(child) {
                    child.style.display = (child.style.display === 'none') ? '' : 'none';
                });
            }
        });
    });

    // Check saved cookie states
    if (getCookie('kivy.toggledesc') === 'true') {
        document.querySelectorAll('div.body dl.api-level > dd > dl > dd').forEach(el => el.style.display = 'none');
        if (toggleDescBtn) {
            toggleDescBtn.classList.remove('showed');
            toggleDescBtn.innerHTML = 'Show Descriptions &dArr;';
        }
    }

    if (getCookie('kivy.toggleall') === 'true') {
        document.querySelectorAll('div.body dl.api-level > dd').forEach(el => el.style.display = 'none');
        var apiToggle = document.getElementById('api-toggle');
        if (apiToggle) {
            apiToggle.classList.remove('showed');
            apiToggle.innerHTML = 'Expand All &dArr;';
        }
    }

    //----------------------------------------------------------------------------
    // Reduce the TOC page
    //----------------------------------------------------------------------------
    var headers = document.querySelectorAll('div.sphinxsidebarwrapper h3');
    if (headers.length >= 2) {
        var targetH3 = headers[1];
        var nextUl = targetH3.nextElementSibling;
        if (nextUl && nextUl.tagName === 'UL') {
            var nestedUl = nextUl.querySelector('li > ul');
            if (nestedUl) {
                nextUl.remove();
                targetH3.after(nestedUl);
            }
        }
    }

    document.querySelectorAll("div.sphinxsidebarwrapper ul").forEach(function(ul) {
        if (ul.children.length < 1) ul.remove();
    });

    //----------------------------------------------------------------------------
    // Menu navigation
    //----------------------------------------------------------------------------
    var mainLinks = document.querySelectorAll('div.sphinxsidebarwrapper > ul > li > a');
    mainLinks.forEach(function(item) {
        item.setAttribute('href', '#');
        item.classList.add('mainlevel');
        
        if (!is_api) {
            item.addEventListener('mousedown', function() {
                var parentLi = this.parentElement;
                var currentChildUl = parentLi ? parentLi.querySelector('ul') : null;
                
                document.querySelectorAll('div.sphinxsidebar ul li ul').forEach(function(child) {
                    if (child !== currentChildUl) child.style.display = 'none';
                });
                
                if (currentChildUl) {
                    currentChildUl.style.display = (currentChildUl.style.display === 'none' || currentChildUl.style.display === '') ? 'block' : 'none';
                }
            });
        }
    });

    var currentLi = document.querySelector('div.sphinxsidebarwrapper li.current');
    if (currentLi && currentLi.parentElement) {
        currentLi.parentElement.style.display = 'block';
    }

    if (!is_api) {
        document.querySelectorAll('div.sphinxsidebarwrapper ul li').forEach(function(item) {
            if (item.querySelectorAll('ul').length > 0) {
                var childA = item.querySelector('a');
                if (childA) childA.classList.add('togglable');
            }
        });
    }

    // Apply tracking labels
    document.querySelectorAll('div.sphinxsidebar a[href$="api-kivy.html"], div.sphinxsidebar a[href$="api-kivy.utils.html"]').forEach(function(el) {
        if (el.parentElement && el.parentElement.parentElement) {
            el.parentElement.parentElement.classList.add('api-index');
        }
    });

    var currentL2 = document.querySelectorAll('li.current.toctree-l2');
    if (currentL2.length > 1) {
        for (var i = 0; i < currentL2.length - 1; i++) {
            currentL2[i].classList.remove('current');
        }
    }

    document.querySelectorAll('ul.api-index a').forEach(function(item) {
        var href = item.getAttribute('href') || '';
        var url = href.slice(0, -5);
        if (url === '') {
            item.setAttribute('href', location.pathname);
            url = location.pathname.slice(0, -5);
        }
        var searchIndex = url.search('api-');
        url = url.substring(searchIndex !== -1 ? searchIndex + 4 : 0);
        item.innerHTML = '';
        item.textContent = url;
    });

    // Hide sections based on page classification routing context
    if (is_api) {
        document.querySelectorAll('div.sphinxsidebarwrapper > ul > li > ul').forEach(function(item) {
            if (!item.classList.contains('api-index') && item.parentElement) {
                item.parentElement.style.display = 'none';
            }
        });
        var navApi = document.querySelector('.nav-api');
        if (navApi) navApi.classList.add('current');
        document.body.classList.add('is-api');
    } else {
        document.querySelectorAll('div.sphinxsidebarwrapper > ul > li > ul').forEach(function(item) {
            if (item.classList.contains('api-index') && item.parentElement) {
                item.parentElement.style.display = 'none';
            }
        });
        var navGuides = document.querySelector('.nav-guides');
        if (navGuides) navGuides.classList.add('current');
    }

    if (is_api) {
        var tocDiv = document.querySelector('.toc');
        if (tocDiv) tocDiv.style.display = 'none';

        function read_version(item, default_version) {
            if (!item) return default_version;
            var pTag = item.querySelector('p');
            var version = pTag ? pTag.textContent.trim() : "";
            if (version === "") return default_version;
            
            item.remove();
            version = version.replace('New in version ', '');
            if (version.endsWith('.')) {
                version = version.slice(0, -1);
            }
            return version;
        }

        var module_version = read_version(document.querySelector('div.body > div.section > div.versionadded'), '1.0.0');
        var html_version = '<span class="versionadded">Added in <span>' + module_version + '</span></span>';
        
        var shortcutDiv = document.querySelector('div.bodyshortcut');
        if (shortcutDiv) shortcutDiv.insertAdjacentHTML('beforeend', html_version);

        document.querySelectorAll('div.section > dl[class]').forEach(function(el_class) {
            var class_version = read_version(el_class.querySelector('> dd > div.versionadded'), module_version);
            var html_class_version = '<span class="versionadded">Added in <span>' + class_version + '</span></span>';
            
            var classDt = el_class.querySelector('> dt');
            if (classDt) classDt.insertAdjacentHTML('beforeend', html_class_version);

            el_class.querySelectorAll('> dd > dl[class]').forEach(function(el_methattr) {
                var methattr_version = read_version(el_methattr.querySelector('> dd > div.versionadded'), class_version);
                var html_methattr_version = '<span class="versionadded">Added in <span>' + methattr_version + '</span></span>';
                
                var methattrDt = el_methattr.querySelector('> dt');
                if (methattrDt) methattrDt.insertAdjacentHTML('beforeend', html_methattr_version);
            });
        });

    } else {
        var tocUls = document.querySelectorAll('.toc > ul > li > ul');
        var tocDiv = document.querySelector('.toc');
        if (tocUls.length < 1 && tocDiv) {
            tocDiv.style.display = 'none';
        }

        var currentLiA = document.querySelector('li.toctree-l1.current > a');
        var section_title = currentLiA ? currentLiA.textContent : '';
        var firstH1 = document.querySelector('div.body h1');
        if (firstH1 && section_title) {
            firstH1.insertAdjacentHTML('afterbegin', section_title + ' &raquo; ');
        }
    }

    // Code snippet lineno stripping patch
    document.querySelectorAll(".linenos, .gp").forEach(function(elem) {
        elem.setAttribute("unselectable-data", elem.textContent.trim());
        
        Array.from(elem.childNodes).forEach(function(child) {
            if (child.nodeType === 3) { // Text node check
                child.remove();
            }
        });
    });

    // Modern light/dark style wrapper configuration toggle
    var themeToggle = document.getElementById("themeToggleSwitch");
    if (themeToggle) {
        themeToggle.addEventListener("click", function() {
            let currTheme = document.documentElement.className,
                newTheme = currTheme === "light" ? "dark" : "light";
            document.documentElement.className = newTheme;
            localStorage.setItem('theme', newTheme);
        });
    }
});