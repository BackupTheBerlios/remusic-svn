<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:sql="http://remus.sourceforge.net/xml/sql/1.0"
                version="1.0">

  <xsl:output method="text"/>

  <xsl:template match="/">
    <xsl:text>#
# This file generated from an XML file describing the database.
#
# Do not edit.
#
# Process with 'dot -Tpng -o graph.png &lt;file>' to make
# a PNG image.
#
</xsl:text>
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="sql:database">
    <xsl:text>digraph </xsl:text>
    <xsl:value-of select="sql:name"/><xsl:text> {
    rankdir = LR;
    node [shape=record, fontname="Courier"];
</xsl:text>
    <xsl:apply-templates select="sql:table"/>
    <xsl:text>
}
</xsl:text>
  </xsl:template>

  <xsl:template match="sql:table">
    <xsl:text>    </xsl:text>
    <xsl:value-of select="sql:name"/>
    <xsl:text> [
        label="</xsl:text>
    <xsl:value-of select="sql:name"/>
    <xsl:text> | {{</xsl:text>
    <xsl:apply-templates select="sql:columns" mode="names"/>
    <xsl:text>} | {</xsl:text>
    <xsl:apply-templates select="sql:columns" mode="types"/>
    <xsl:text>}}"</xsl:text>
    <xsl:text>
        ];
</xsl:text>

    <!-- Now, draw edges -->
    <xsl:apply-templates select="sql:columns" mode="edges"/>
  </xsl:template>

  <xsl:template match="sql:columns" mode="names">
    <xsl:apply-templates select="sql:column" mode="names"/>
  </xsl:template>

  <xsl:template match="sql:column" mode="names">
    <xsl:if test="sql:type/@primary-key">
      <xsl:text>&lt;key> </xsl:text>
    </xsl:if>
    <xsl:value-of select="@name"/>
    <xsl:if test="position() != last()">
      <xsl:text> | </xsl:text>
    </xsl:if>
  </xsl:template>

  <xsl:template match="sql:columns" mode="types">
    <xsl:apply-templates select="sql:column" mode="types"/>
  </xsl:template>

  <xsl:template match="sql:column" mode="types">
    <xsl:apply-templates select="sql:type"/>
    <xsl:if test="position() != last()">
      <xsl:text> | </xsl:text>
    </xsl:if>
  </xsl:template>

  <xsl:template match="sql:type">
    <xsl:choose>
      <xsl:when test="sql:key">
        <xsl:text>&lt;</xsl:text>
        <xsl:value-of select="sql:key/@table"/>
        <xsl:text>></xsl:text>
        <xsl:text>RELATION</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="normalize-space(.)"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="sql:columns" mode="edges">
    <xsl:apply-templates select="sql:column" mode="edges"/>
  </xsl:template>

  <xsl:template match="sql:column" mode="edges">
    <xsl:apply-templates select="sql:type" mode="edges"/>
  </xsl:template>

  <xsl:template match="sql:type" mode="edges">
    <xsl:if test="sql:key">
      <xsl:value-of select="ancestor::sql:table/sql:name"/>
      <xsl:text>:</xsl:text>
      <xsl:value-of select="sql:key/@table"/>
      <xsl:text> -> </xsl:text>
      <xsl:value-of select="sql:key/@table"/>
      <xsl:text>:key;
</xsl:text>
    </xsl:if>
  </xsl:template>
</xsl:stylesheet>
