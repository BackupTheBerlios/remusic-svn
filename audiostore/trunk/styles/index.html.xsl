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
  

  <xsl:param name="l10n.gentext.default.language" select="'en'"/>
  <xsl:param name="l10n.gentext.language" select="''"/>
  <xsl:param name="l10n.gentext.use.xref.language" select="0"/>

  <xsl:include href="l10n.xsl"/>
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
        <title>
          <xsl:call-template name="gentext">
            <xsl:with-param name="key" select="'page.title'"/>
          </xsl:call-template>
        </title>
        <meta name="generator" content="REMUS audiostore"/>
        <link rel="stylesheet" href="/styles/remus.css" type="text/css"/>
        <link rel="stylesheet" href="/styles/audiostore.css" type="text/css"/>
	<script type="text/javascript" language="JavaScript" src="/scripts/menu.js"></script>
	
      </head>
      <body onclick="menu.hideMenus()">
        <div class="logo">
          &amp;<span style="color:red">re:</span><i>MUS</i><span style="color:blue">ic</span>;
        </div>
        <hr/>

        <!-- Menu placeholder -->
	<menu/>

        <h2>
          <xsl:call-template name="gentext">
            <xsl:with-param name="key" select="'MusicFrom'"/>
          </xsl:call-template>
          <xsl:text> </xsl:text>
          <xsl:apply-templates select=".//path"/>
        </h2>

	<xsl:variable name="relurl">
	  <xsl:choose>
	    <xsl:when test="audiolist">
	      <xsl:text>../</xsl:text>
	    </xsl:when>
	  </xsl:choose>
	</xsl:variable>

        <div class="navigation">
          <a href="{$audiostore.root}">
            <xsl:attribute name="title">
              <xsl:call-template name="gentext">
                <xsl:with-param name="key" select="'root.link.title'"/>
              </xsl:call-template>
            </xsl:attribute>
            <xsl:choose>
              <xsl:when test="$home.image != ''">
                <img>
                  <xsl:attribute name="src">
                    <xsl:value-of select="$home.image"/>
                  </xsl:attribute>
                </img>
              </xsl:when>
              <xsl:otherwise>
                <xsl:call-template name="gentext">
                  <xsl:with-param name="key" select="'Home'"/>
                </xsl:call-template>
              </xsl:otherwise>
            </xsl:choose>
          </a>
          <xsl:text>|</xsl:text>
          <a href="{$audiostore.root}artist/">
            <xsl:attribute name="title">
              <xsl:call-template name="gentext">
                <xsl:with-param name="key" select="'artist.link.title'"/>
              </xsl:call-template>
            </xsl:attribute>
            <xsl:choose>
              <xsl:when test="$artists.image != ''">
                <img>
                  <xsl:attribute name="src">
                    <xsl:value-of select="$artists.image"/>
                  </xsl:attribute>
                </img>
              </xsl:when>
              <xsl:otherwise>
                <xsl:call-template name="gentext">
                  <xsl:with-param name="key" select="'Artists'"/>
                </xsl:call-template>
              </xsl:otherwise>
            </xsl:choose>
          </a>
          <xsl:text>|</xsl:text>
          <a href="{$audiostore.root}album/">
            <xsl:attribute name="title">
              <xsl:call-template name="gentext">
                <xsl:with-param name="key" select="'album.link.title'"/>
              </xsl:call-template>
            </xsl:attribute>
            <xsl:choose>
              <xsl:when test="$albums.image != ''">
                <img>
                  <xsl:attribute name="src">
                    <xsl:value-of select="$albums.image"/>
                  </xsl:attribute>
                </img>
              </xsl:when>
              <xsl:otherwise>
                <xsl:call-template name="gentext">
                  <xsl:with-param name="key" select="'Albums'"/>
                </xsl:call-template>
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
                    <xsl:call-template name="gentext">
                      <xsl:with-param name="key" select="'DirList'"/>
                    </xsl:call-template>
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
                    <xsl:call-template name="gentext">
                      <xsl:with-param name="key" select="'Songlist'"/>
                    </xsl:call-template>
		  </xsl:otherwise>
		</xsl:choose> 
	      </xsl:when>
	    </xsl:choose>
	  </xsl:variable>
	  <xsl:variable name="linktitle">
	    <xsl:choose>
	      <xsl:when test="audiolist">
                <xsl:call-template name="gentext">
                  <xsl:with-param name="key" select="'dirlist.link.title'"/>
                </xsl:call-template>
	      </xsl:when>
	      <xsl:when test="dirlisting">
                <xsl:call-template name="gentext">
                  <xsl:with-param name="key" select="'songlist.link.title'"/>
                </xsl:call-template>
	      </xsl:when>
	    </xsl:choose>
	  </xsl:variable>
          <a title="{$linktitle}" href="{$url}">
	    <xsl:value-of select="$linktext"/>
          </a>
          <xsl:text>|</xsl:text>
          <a>
            <xsl:attribute name="title">
              <xsl:call-template name="gentext">
                <xsl:with-param name="key" select="'m3u.link.title'"/>
              </xsl:call-template>
            </xsl:attribute>
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
                <xsl:call-template name="gentext">
                  <xsl:with-param name="key" select="'m3u.title'"/>
                </xsl:call-template>
              </xsl:otherwise>
            </xsl:choose>
          </a>
          <xsl:text>|</xsl:text>
          <a>
            <xsl:attribute name="title">
              <xsl:call-template name="gentext">
                <xsl:with-param name="key" select="'remus.link.title'"/>
              </xsl:call-template>
            </xsl:attribute>
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
                <xsl:call-template name="gentext">
                  <xsl:with-param name="key" select="'remus.title'"/>
                </xsl:call-template>
              </xsl:otherwise>
            </xsl:choose>
          </a>
        </div>
        
        <xsl:apply-templates/>
        
        <hr/>
        
        <div class="generated">
          <xsl:call-template name="gentext">
            <xsl:with-param name="key" select="'Generated'"/>
          </xsl:call-template>
          <xsl:text> </xsl:text>
          <a href="{$remus.url}">
            <xsl:text>remus.audiostore </xsl:text>
	    <xsl:value-of select="$remus.version"/>
          </a>
          <xsl:text> </xsl:text>
          <xsl:call-template name="gentext">
            <xsl:with-param name="key" select="'FromTheStore'"/>
          </xsl:call-template>
          <xsl:text> </xsl:text>
          <a href="{$audiostore.url}">
            <xsl:value-of select="$audiostore.url"/>
          </a>
        </div>

	<div id="portal-colophon">
	  <ul>
	    <li>
	      <a href="http://validator.w3.org/check/referer">
		<img src="/images/valid_xhtml.png"
		     height="15" width="80" alt="Valid XHTML"
		     title="This site is valid XHTML." />
	      </a>
	    </li>
	    <li>
	      <a href="http://jigsaw.w3.org/css-validator/check/referer">
		<img src="/images/valid_css.png"
		     height="15" width="80" alt="Valid CSS"
		     title="This site was built with valid CSS." />
	      </a>
	    </li>
	    
	    <li>
	      <a href="http://www.anybrowser.org/campaign/">
		<img src="/images/anybrowser.png"
		     height="15" width="80"
		     alt="Usable in any browser"
		     title="This site is usable in any web browser." />
	      </a>
	    </li>
	  </ul>  
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
            <a href="?order=remus_artists.art_sortname&amp;order=remus_albums.alb_name&amp;order=remus_audio_objects.au_track_number">
              <xsl:call-template name="gentext">
                <xsl:with-param name="key" select="'Artist'"/>
              </xsl:call-template>
	    </a>
          </th>
          <th>
            <a href="?order=remus_albums.alb_name&amp;order=remus_audio_objects.au_track_number">
              <xsl:call-template name="gentext">
                <xsl:with-param name="key" select="'Album'"/>
              </xsl:call-template>
            </a>
          </th>
          <th>
            <a href="?order=remus_audio_objects.au_title">
              <xsl:call-template name="gentext">
                <xsl:with-param name="key" select="'Song'"/>
              </xsl:call-template>
            </a>
          </th>
          <th>
            <a href="?order=remus_audio_objects.au_length">
              <xsl:call-template name="gentext">
                <xsl:with-param name="key" select="'Time'"/>
              </xsl:call-template>
            </a>
          </th>
        </tr>
        <tr class="subtitle">
          <th colspan="4">
            <xsl:call-template name="gentext">
              <xsl:with-param name="key" select="'NumberOfSongs'"/>
            </xsl:call-template>
            <xsl:text>: </xsl:text><xsl:value-of select="@length"/>
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
            <xsl:text>/list/index.html</xsl:text>
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
	<th>
          <xsl:call-template name="gentext">
            <xsl:with-param name="key" select="'Count'"/>
          </xsl:call-template>
        </th>
      </tr>
      <tr class="subtitle">
	<th>
	  <xsl:attribute name="colspan">
	    <xsl:value-of select="@cols+1"/>
	  </xsl:attribute>
          <xsl:call-template name="gentext">
            <xsl:with-param name="key" select="'NumberOfItems'"/>
          </xsl:call-template>
          <xsl:text>: </xsl:text>
          <xsl:value-of select="../@length"/>
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
        <xsl:call-template name="gentext">
          <xsl:with-param name="key">
            <xsl:value-of select="."/>
          </xsl:with-param>
        </xsl:call-template>
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
