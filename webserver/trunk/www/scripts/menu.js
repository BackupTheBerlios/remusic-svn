/* -*- Mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*-
 *
 * Copyright (C) 2004 Daniel Larsson
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Library General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Library General Public License for more details.
 *
 * You should have received a copy of the GNU Library General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */


//
// Manage menu identified by 'element'
//
function RemusMenu(element)
{
    this.menu = element;
    
    for(var i = 0; i < this.menu.childNodes.length; ++i) {
        var child = this.menu.childNodes[i];
        child.onclick = this.openMenu;
    }    
}

RemusMenu.prototype.openMenu = function(element) {
    var children = this.menu.getElementsByTagName("span") // childNodes[i];
    for(var i = 0; i < children.length; ++i) {
        var child = children[i];
        if (child != element) {
            this.hideMenu(child);
        } else {
            this.toggleMenu(child);
        }
    }
}

RemusMenu.prototype.toggleMenu = function(element) {
    var id = element.id + "_menu";
    var menu = document.getElementById(id);
    if (menu) {
        if (menu.style) {
            if (menu.style.visibility == 'visible') {
                this.hideMenu(element);
            } else {
                this.showMenu(element);
            }
        }
    }
}

RemusMenu.prototype.showMenu = function(element) {
    var id = element.id + "_menu";
    var menu = document.getElementById(id);
    if (menu) {
        if (menu.style) {
            alert(element.offsetLeft + ", " + element.offsetTop);
            alert(element.innerHTML);
            var x = element.offsetLeft + document.body.scrollLeft;
            var y = element.offsetTop + element.offsetHeight + document.body.scrollTop + 5;
            menu.style.top = y+"px";
            menu.style.left = x+"px";
            menu.style.visibility = 'visible';
        }
    }
}

RemusMenu.prototype.hideMenu = function(element) {
    var id = element.id + "_menu";
    var menu = document.getElementById(id);
    if (menu) {
        if (menu.style) {
            menu.style.visibility = 'hidden';
        }
    }
}
