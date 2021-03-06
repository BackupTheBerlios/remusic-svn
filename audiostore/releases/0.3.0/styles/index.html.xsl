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

     Creates web pages from the database.

-->

<xsl:stylesheet 
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:doc="http://nwalsh.com/xsl/documentation/1.0"
  exclude-result-prefixes="doc"
  version="1.0">
  
  <xsl:output
    method="xml"
    encoding="UTF-8"
    indent="yes"
    doctype-public="-//W3C//DTD XHTML 1.0 Transitional//EN"
    doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"/>
  
  
  <xsl:include href="param.xsl"/>

  <xsl:template match="d">
    <xsl:param name="path"/>
    
    <a xmlns="http://www.w3.org/1999/xhtml">
      <xsl:attribute name="href">
	<xsl:value-of select="$path"/><xsl:value-of select="."/>/
      </xsl:attribute>
      <xsl:value-of select="."/>
    </a>
    <xsl:if test="following-sibling::d">
      <xsl:text>/</xsl:text>
      <xsl:apply-templates select="following-sibling::d[position()=1]">
	<xsl:with-param name="path">
	  <xsl:value-of select="$path"/><xsl:value-of select="."/>/
	</xsl:with-param>
      </xsl:apply-templates>
    </xsl:if>
  </xsl:template>

  <xsl:template match="path">
    <xsl:variable name="path" select="$audiostore.root"/>

    <xsl:choose>
      <xsl:when test="d">
	<xsl:apply-templates select="d[position()=1]">
	  <xsl:with-param name="path">
	    <xsl:value-of select="$path"/>
	  </xsl:with-param>
	</xsl:apply-templates>
      </xsl:when>
      <xsl:otherwise>
	<xsl:text>/</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="/">
    <html xmlns="http://www.w3.org/1999/xhtml">
      <head>
        <title>REMUS audio listing</title>
        <meta name="generator" content="REMUS audiostore"/>
        <link rel="stylesheet" href="/styles/remus.css" type="text/css"/>
        <link rel="stylesheet" href="/styles/audiostore.css" type="text/css"/>
      </head>
      <body>
        <div class="logo">
          &amp;<span style="color:red">re:</span><i>MUS</i><span style="color:blue">ic</span>;
        </div>
        <hr/>
        <h2>Music from <xsl:apply-templates select=".//path"/></h2>

	<xsl:variable name="relurl">
	  <xsl:choose>
	    <xsl:when test="audiolist">
	      <xsl:text>../</xsl:text>
	    </xsl:when>
	  </xsl:choose>
	</xsl:variable>

        <div class="navigation">
          <a title="Top of the music tree" href="{$audiostore.root}">
            <xsl:choose>
              <xsl:when test="$home.image != ''">
                <img>
                  <xsl:attribute name="src">
                    <xsl:value-of select="$home.image"/>
                  </xsl:attribute>
                </img>
              </xsl:when>
              <xsl:otherwise>
                <xsl:text>Home</xsl:text>
              </xsl:otherwise>
            </xsl:choose>
          </a>
          <xsl:text>|</xsl:text>
          <a title="List of all artists" href="{$audiostore.root}artist/">
            <xsl:choose>
              <xsl:when test="$artists.image != ''">
                <img>
                  <xsl:attribute name="src">
                    <xsl:value-of select="$artists.image"/>
                  </xsl:attribute>
                </img>
              </xsl:when>
              <xsl:otherwise>
                <xsl:text>Artists</xsl:text>
              </xsl:otherwise>
            </xsl:choose>
          </a>
          <xsl:text>|</xsl:text>
          <a title="List of all albums" href="{$audiostore.root}album/">
            <xsl:choose>
              <xsl:when test="$albums.image != ''">
                <img>
                  <xsl:attribute name="src">
                    <xsl:value-of select="$albums.image"/>
                  </xsl:attribute>
                </img>
              </xsl:when>
              <xsl:otherwise>
                <xsl:text>Albums</xsl:text>
              </xsl:otherwise>
            </xsl:choose>
          </a>
          <xsl:text>|</xsl:text>
	  <xsl:variable name="url">
	    <xsl:choose>
	      <xsl:when test="audiolist">
		..
	      </xsl:when>
	      <xsl:when test="dirlisting">
		list/index.html
	      </xsl:when>
	    </xsl:choose>
	  </xsl:variable>
	  <xsl:variable name="linktext">
	    <xsl:choose>
	      <xsl:when test="audiolist">
		<xsl:choose>
		  <xsl:when test="$playlist.dirlist.image != ''">
		    <img>
		      <xsl:attribute name="src">
			<xsl:value-of select="$playlist.dirlist.image"/>
		      </xsl:attribute>
		    </img>
		  </xsl:when>
		  <xsl:otherwise>
		    <xsl:text>Directory list</xsl:text>
		  </xsl:otherwise>
		</xsl:choose>
	      </xsl:when>
	      <xsl:when test="dirlisting">
		<xsl:choose>
		  <xsl:when test="$playlist.songlist.image != ''">
		    <img>
		      <xsl:attribute name="src">
			<xsl:value-of select="$playlist.songlist.image"/>
		      </xsl:attribute>
		    </img>
		  </xsl:when>
		  <xsl:otherwise>
		    <xsl:text>Song list</xsl:text>
		  </xsl:otherwise>
		</xsl:choose> 
	      </xsl:when>
	    </xsl:choose>
	  </xsl:variable>
	  <xsl:variable name="linktitle">
	    <xsl:choose>
	      <xsl:when test="audiolist">
		<xsl:text>List the contents in this directory</xsl:text>
	      </xsl:when>
	      <xsl:when test="dirlisting">
		<xsl:text>List all songs in this scope (potentially a long list)</xsl:text>
	      </xsl:when>
	    </xsl:choose>
	  </xsl:variable>
          <a title="{$linktitle}" href="{$url}">
	    <xsl:value-of select="$linktext"/>
          </a>
          <xsl:text>|</xsl:text>
          <a title="Playlist in extended M3U format (most players support this)">
            <xsl:attribute name="href">
	      <xsl:value-of select="$relurl"/><xsl:text>list/list.m3u</xsl:text>
            </xsl:attribute>
            <xsl:choose>
              <xsl:when test="$playlist.m3u.image != ''">
                <img>
                  <xsl:attribute name="src">
                    <xsl:value-of select="$playlist.m3u.image"/>
                  </xsl:attribute>
                </img>
              </xsl:when>
              <xsl:otherwise>
                <xsl:text>Playlist (m3u)</xsl:text>
              </xsl:otherwise>
            </xsl:choose>
          </a>
          <xsl:text>|</xsl:text>
          <a title="Playlist in remus format (internal format, used by the remus player)">
            <xsl:attribute name="href">
	      <xsl:value-of select="$relurl"/><xsl:text>list/remus</xsl:text>
            </xsl:attribute>
            <xsl:choose>
              <xsl:when test="$playlist.remus.image != ''">
                <img>
                  <xsl:attribute name="src">
                    <xsl:value-of select="$playlist.remus.image"/>
                  </xsl:attribute>
                </img>
              </xsl:when>
              <xsl:otherwise>
                <xsl:text>Playlist (remus)</xsl:text>
              </xsl:otherwise>
            </xsl:choose>
          </a>
        </div>
        
        <xsl:apply-templates/>
        
        <hr/>
        
        <div class="generated">
          <xsl:text>Generated by </xsl:text>
          <a href="{$remus.url}">
            <xsl:text>remus.audiostore </xsl:text>
	    <xsl:value-of select="$remus.version"/>
          </a>
          <xsl:text> from the audiostore at </xsl:text>
          <a href="{$audiostore.url}">
            <xsl:value-of select="$audiostore.url"/>
          </a>
        </div>
      </body>
    </html>
  </xsl:template>

  <xsl:template match="audiolist">
    <table xmlns="http://www.w3.org/1999/xhtml"
	   class="audiolist"
	   cellspacing="0">
      <thead>
        <tr class="colhead">
          <th>
            <a href="?order=art_sortname&amp;order=alb_name&amp;order=au_track_number">
	      Artist:
	    </a>
          </th>
          <th>
            <a href="?order=alb_name&amp;order=au_track_number">Album: </a>
          </th>
          <th>
            <a href="?order=au_title">Song:</a>
          </th>
          <th>
            <a href="?order=au_length">Time:</a>
          </th>
        </tr>
        <tr class="subtitle">
          <th colspan="4">
	    Number of songs: <xsl:value-of select="@length"/>
	  </th>
        </tr>
      </thead>
      <tbody>
        <xsl:apply-templates select="audioclip"/>
      </tbody>
    </table>
  </xsl:template>


  <xsl:template match="audioclip">
    <tr xmlns="http://www.w3.org/1999/xhtml">
      <xsl:attribute name="class">
        <xsl:choose>
          <xsl:when test="position() mod 2 = 0">
            <xsl:text>even</xsl:text>
          </xsl:when>
          <xsl:otherwise>
            <xsl:text>odd</xsl:text>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:attribute>
      <td>
        <a class="musiclink">
          <xsl:attribute name="href">
            <xsl:value-of select="$audiostore.root"/>
	    <xsl:text>artist/</xsl:text>
	    <xsl:value-of select="artist"/>
	    <xsl:text>/</xsl:text>
          </xsl:attribute>
          <xsl:value-of select="artist"/>
        </a>
      </td>
      <td>
        <a class="musiclink">
          <xsl:attribute name="href">
            <xsl:value-of select="$audiostore.root"/>
	    <xsl:text>album/</xsl:text>
	    <xsl:value-of select="album"/>
	    <xsl:text>/</xsl:text>
          </xsl:attribute>
          <xsl:value-of select="album"/>
        </a>
      </td>
      <td>
        <a class="musiclink">
          <xsl:attribute name="href">
            <xsl:value-of select="$audiostore.root"/><xsl:value-of select="filename"/>
          </xsl:attribute>
          <xsl:value-of select="title"/>
        </a>
      </td>
      <td><xsl:value-of select="length"/></td>
    </tr>
  </xsl:template>


  <xsl:template match="dirlisting">
    <table xmlns="http://www.w3.org/1999/xhtml"
	   class="audiolist"
	   cellspacing="0">
      <xsl:apply-templates select="columns"/>
      <tbody>
        <xsl:apply-templates select="item"/>
      </tbody>
    </table>
  </xsl:template>

  <xsl:template match="columns">
    <thead xmlns="http://www.w3.org/1999/xhtml">
      <tr class="colhead">
	<xsl:apply-templates/>
	<th>Count</th>
      </tr>
      <tr class="subtitle">
	<th>
	  <xsl:attribute name="colspan">
	    <xsl:value-of select="@cols+1"/>
	  </xsl:attribute>
	  Number of items: <xsl:value-of select="../@length"/>
	</th>
      </tr>
    </thead>
  </xsl:template>

  <xsl:template match="column">
    <th xmlns="http://www.w3.org/1999/xhtml">
      <a>
	<xsl:attribute name="href">
	  <xsl:text>?order=</xsl:text><xsl:value-of select="@key"/>
	</xsl:attribute>
	<xsl:value-of select="."/>
      </a>
    </th>
  </xsl:template>

  <xsl:template match="item">
    <tr xmlns="http://www.w3.org/1999/xhtml">
      <xsl:attribute name="class">
        <xsl:choose>
          <xsl:when test="position() mod 2 = 0">
            <xsl:text>even</xsl:text>
          </xsl:when>
          <xsl:otherwise>
            <xsl:text>odd</xsl:text>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:attribute>

      <xsl:apply-templates/>
      <td style="text-align:right"><xsl:value-of select="@length"/></td>
    </tr>
  </xsl:template>

  <xsl:template match="*">
    <td xmlns="http://www.w3.org/1999/xhtml">
      <xsl:choose>
	<xsl:when test="@link">
	  <a>
	    <xsl:attribute name="href">
	      <xsl:value-of select="@link"/>
	    </xsl:attribute>
	    <xsl:value-of select="."/>
	  </a>
	</xsl:when>
	<xsl:otherwise>
	  <xsl:value-of select="."/>
	</xsl:otherwise>
      </xsl:choose>
    </td>
  </xsl:template>
</xsl:stylesheet>
