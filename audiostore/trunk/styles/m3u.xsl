<?xml version="1.0" encoding="US-ASCII"?>

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
