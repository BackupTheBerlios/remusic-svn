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

     Create m3u playlists.

-->

<xsl:stylesheet 
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version="1.0">
  
  <xsl:output
    method="text"
    encoding="UTF-8"
    indent="yes"/>


  <xsl:template match="/">
    <xsl:apply-templates select="audiolist"/>
  </xsl:template>


  <xsl:template match="audiolist">
    <xsl:text>#EXTM3U
</xsl:text>
    <xsl:apply-templates select="audioclip"/>
  </xsl:template>


  <xsl:template match="audioclip">
    <xsl:text>#EXTINF:</xsl:text> <xsl:value-of select="length-in-sec"/>,<xsl:value-of select="artist"/> - <xsl:value-of select="title"/><xsl:text>
</xsl:text>
<xsl:value-of select="filename"/><xsl:text>
</xsl:text>
  </xsl:template>

</xsl:stylesheet>
