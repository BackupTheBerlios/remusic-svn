<?xml version="1.0" encoding="utf-8"?>

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

     Create a Remus playlist.  Experimental format used by the remus
     player.

-->

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">

  <xsl:output method="xml" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/">
      <xsl:apply-templates select="audiolist"/>
  </xsl:template>

  <xsl:template match="audiolist">
    <playlist>
      <xsl:apply-templates select="audioclip"/>
    </playlist>
  </xsl:template>

  <xsl:template match="audioclip">
    <song>
      <title><xsl:value-of select="title"/></title>
      <artist><xsl:value-of select="artist"/></artist>
      <length><xsl:value-of select="length-in-sec"/></length>
      <url><xsl:value-of select="filename"/></url>
    </song>
  </xsl:template>

</xsl:stylesheet>
