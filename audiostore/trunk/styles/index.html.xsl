<?xml version="1.0" encoding="US-ASCII"?>

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
        <h2>Music from <xsl:value-of select="audiolist/path"/></h2>

        <div class="navigation">
          <a href="{$audiostore.root}">
            <xsl:choose>
              <xsl:when test="$home.image != ''">
                <img>
                  <xsl:attribute name="src">
                    <xsl:value-of select="$home.image"/>
                  </xsl:attribute>
                </img>
              </xsl:when>
              <xsl:when test="$home.image = ''">
                <xsl:text>Home</xsl:text>
              </xsl:when>
            </xsl:choose>
          </a>
          <xsl:text>|</xsl:text>
          <a>
            <xsl:attribute name="href">
              <xsl:text>list/m3u</xsl:text>
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
          <a>
            <xsl:attribute name="href">
              <xsl:text>list/remus</xsl:text>
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
        
        <xsl:apply-templates select="audiolist"/>
        
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
            <a href="?order=art_name&amp;order=alb_name&amp;order=au_track_number">
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

</xsl:stylesheet>
