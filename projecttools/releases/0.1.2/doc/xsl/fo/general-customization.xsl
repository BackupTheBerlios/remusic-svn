<?xml version='1.0'?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version='1.0'
                xmlns:fo="http://www.w3.org/1999/XSL/Format"
                >

  <xsl:import href="/usr/local/share/xsl/docbook/fo/docbook.xsl"/>
  <xsl:import href="titlepage.templates.xsl"/>


  <xsl:param name="section.autolabel" select="1"/>
  <xsl:param name="toc.section.depth" select="3"/>
  <xsl:param name="paper.type" select="'A4'"/>
  <xsl:param name="generate.index" select="1"/>
  <xsl:param name="admon.graphics" select="1"/>
  <xsl:param name="use.extensions" select="1"/>
  <xsl:param name="tablecolumns.extension" select="0"/>
  <xsl:param name="passivetex.extensions" select="1"/>
  <xsl:param name="fop.extensions" select="0"/>
  <xsl:param name="double.sided" select="1"/>


  <!-- Insert titlepage matter before the title                           -->
  <!-- Note: This is copied and modified from the generated stylesheet    -->
  <!-- titlepage.template.xsl. If you modify titlepage.template.xml       -->
  <!-- you might need to modify this code as well, to properly reflect    -->
  <!-- your changes.                                                      -->

  <xsl:template match="title" mode="book.titlepage.recto.auto.mode">
    <fo:block xmlns:fo="http://www.w3.org/1999/XSL/Format"
	      text-align="left"
	      font-size="72pt"
	      color="#96c4dd"
	      space-before="20pt"
	      font-weight="bold"
	      margin-left="0.5in - {$page.margin.inner} + {$title.margin.left}"
	      font-family="Helvetica">
      Remus
    </fo:block>
    <fo:block xmlns:fo="http://www.w3.org/1999/XSL/Format"
	      margin-left="0.5in - {$page.margin.inner} + {$title.margin.left}">
      <fo:leader
        leader-pattern="rule"
        leader-length.maximum="190mm"
        leader-length.optimum="190mm"/>
    </fo:block>
    <fo:block xmlns:fo="http://www.w3.org/1999/XSL/Format"
	      xsl:use-attribute-sets="book.titlepage.recto.style"
	      text-align="right"
	      font-size="24.8832pt"
	      space-before="18.6624pt"
	      font-weight="bold"
	      font-family="{$title.fontset}">
      <xsl:call-template name="division.title">
	<xsl:with-param name="node" select="ancestor-or-self::book[1]"/>
      </xsl:call-template>
    </fo:block>
  </xsl:template>

</xsl:stylesheet>
