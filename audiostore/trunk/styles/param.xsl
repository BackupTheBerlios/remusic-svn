<?xml version="1.0" encoding="US-ASCII"?>

<!--

     Copyright (C) 2004 Daniel Larsson

     This library is free software; you can redistribute it and/or
     modify it under the terms of the GNU Library General Public
     License as published by the Free Software Foundation; either
     version 2 of the License, or (at your option) any later version.

     This library is distributed in the hope that it will be useful,
     but WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
     Library General Public License for more details.

     You should have received a copy of the GNU Library General Public
     License along with this library; if not, write to the
     Free Software Foundation, Inc., 59 Temple Place - Suite 330,
     Boston, MA 02111-1307, USA.

     Parameters for the index.html generation.

-->

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">


<xsl:param name="remus.url" select="'http://www.remus.org/'"/>
<xsl:param name="remus.version" select="'0.3.0'"/>
<xsl:param name="audiostore.url" select="'unknown'"/>
<xsl:param name="audiostore.root" select="'/'"/>
<xsl:param name="home.image" select="''"/>
<xsl:param name="albums.image" select="''"/>
<xsl:param name="artists.image" select="''"/>
<xsl:param name="playlist.songlist.image" select="''"/>
<xsl:param name="playlist.dirlist.image" select="''"/>
<xsl:param name="playlist.m3u.image" select="''"/>
<xsl:param name="playlist.remus.image" select="''"/>

</xsl:stylesheet>
