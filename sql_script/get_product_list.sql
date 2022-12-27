DROP TABLE #ValidCustomer
DROP TABLE #ValidInvoiceNo
DROP TABLE #ExcInv
DROP TABLE #ValidInv
DROP TABLE #invoice_data
DROP TABLE #Valid_Invoice



-- Updated invoice table with reorder rank
-- Create reorder column
SELECT 	DISTINCT i.PrepareDate
		, i.InvoiceDate 
		, i.InvoiceNo 
		, i.CustomerCode 
		, id.ProductCode
		, ROW_NUMBER () OVER (PARTITION BY i.CustomerCode, id.ProductCode ORDER BY i.PrepareDate) AS ReorderRank
INTO #Valid_invoice
FROM InvoiceDetails id
INNER JOIN Invoice i ON i.InvoiceNo = id.Invoiceno 
WHERE CustomerCode IS NOT NULL
ORDER BY i.CustomerCode, id.ProductCode



-- Select valid "regular loyalty" customers who have purchased at least 9 invoices 
SELECT 	i.CustomerCode
		, COUNT(DISTINCT i.InvoiceNo) AS InvoiceCount
INTO #ValidCustomer
FROM Customer c
INNER JOIN Invoice i ON i.CustomerCode = c.CustomerCode 
WHERE LoyaltySettingsId = 1
GROUP BY i.CustomerCode 
HAVING COUNT(DISTINCT i.InvoiceNo) > 9

--SELECT *
--FROM #ExcInv
--WHERE InvoiceDate >= '2015-01-01'

-- Invoices to be excluded. Invoices before 2015 or having non-countable products in their basket or having greater than 20 units of an item purchased in an invoice.  
SELECT 	DISTINCT id.Invoiceno
		, i.InvoiceDate
INTO #ExcInv
FROM InvoiceDetails id
INNER JOIN Product p ON id.ProductCode = p.ProductCode
INNER JOIN Invoice i ON i.InvoiceNo = id.Invoiceno 
WHERE (i.InvoiceDate < '2015-01-01') OR (p.PackSize != 'EA' OR id.SalesQTY > 20) 
ORDER BY Invoiceno 

--SELECT COUNT(DISTINCT Invoiceno)
--FROM #ExcInv
--
--SELECT 	vi.Invoiceno
--		, i.InvoiceDate  
--FROM #ValidInv vi
--INNER JOIN Invoice i ON vi.Invoiceno = i.InvoiceNo 
--WHERE InvoiceDate < 2015

--SELECT 	PrepareDate
--		, InvoiceNo 
--		, CustomerCode 
--		, ProductCode 
--		, CASE WHEN ReorderRank > 1 THEN 1 ELSE 0 END AS Reordered
--FROM #Valid_Invoice
--ORDER BY CustomerCode, ProductCode, ReorderRank 
--
--SELECT * 
--FROM #Valid_Invoice
--ORDER BY CustomerCode, ProductCode, ReorderRank  


-- Excluding the invalid invoices from the main invoice table. Result: Valid invoices.
SELECT 	DISTINCT id.Invoiceno
		, id.ProductCode
		, CustomerCode
		, id.PrepareDate
		, id.InvoiceDate
		, CASE WHEN id.ReorderRank > 1 THEN 1 ELSE 0 END AS Reordered
--		, e.Invoiceno 
--		, InvoiceDate
INTO #ValidInv
FROM #Valid_Invoice id 
LEFT JOIN #ExcInv e ON e.Invoiceno = id.Invoiceno 
WHERE e.Invoiceno IS NULL
ORDER BY id.InvoiceNo 

--SELECT 	i.InvoiceNo 
--		, CustomerCode
--		, id.ProductCode
--		, i.PrepareDate 
--FROM Invoice i 
--INNER JOIN InvoiceDetails id ON id.Invoiceno =i.InvoiceNo 
--WHERE id.ProductCode = '4203132' AND CustomerCode = '99061413'
--DROP TABLE #ValidInvoiceNo
--
--SELECT 	DayTimeFlag
--		, COUNT(DISTINCT InvoiceNo) 
--FROM #ValidInvoiceNo
--GROUP BY DayTimeFlag 
--
--SELECT * FROM #ValidInvoiceNo

-- Further filtering invoices. Only include those invoices having at least 2 and maximum of 50 products. Add columns for Weekend Flag and daytime flag.
SELECT 	DISTINCT i.InvoiceNo 
		, i.CustomerCode 
--		, p.PackSize 
--		, COUNT(id.ProductCode)
--		, DATEPART(hour, i.PrepareDate) 
		, i.PrepareDate
		, CASE WHEN DATENAME (DW,i.InvoiceDate)='Friday' OR DATENAME (DW,i.InvoiceDate)='Saturday' THEN 1 ELSE 0 END AS WeekEndFlag
		, CASE 	WHEN DATEPART(hour, PrepareDate)<=12 THEN 'Morning' 
				WHEN DATEPART(hour, PrepareDate)>12 AND DATEPART(hour, PrepareDate)<=17 THEN 'Afternoon'
				WHEN DATEPART(hour, PrepareDate)>17 AND DATEPART(hour, PrepareDate)<=20 THEN 'Evening'
				WHEN DATEPART(hour, PrepareDate)>20 THEN 'Night'
			END AS DayTimeFlag
		, i.Reordered
INTO #ValidInvoiceNo
FROM #ValidInv i 
INNER JOIN #ValidCustomer vc ON vc.CustomerCode = i.CustomerCode  
GROUP BY 	i.InvoiceNo
			, i.Reordered  
			, i.CustomerCode 
			, i.PrepareDate
			, i.InvoiceDate 
HAVING COUNT(i.ProductCode) > 2 AND COUNT(i.ProductCode) < 50 

 

-- Final invoice table to be exported. 
SELECT	id.Invoiceno
		, i.CustomerCode 
		, id.ProductCode
		, p.ProductName
		, id.SalesQTY 
		, i.PrepareDate
		, i.WeekEndFlag 
		, i.DayTimeFlag
		, i.Reordered 
INTO #invoice_data
FROM InvoiceDetails id
INNER JOIN #ValidInvoiceNo i ON i.InvoiceNo = id.Invoiceno 
INNER JOIN Product p ON p.ProductCode = id.ProductCode 
WHERE  	p.PackSize = 'EA'
		AND (id.SalesQTY >= 1 AND SalesQTY < 20)

		
SELECT *
FROM #invoice_data
ORDER BY CustomerCode, PrepareDate ASC   


SELECT *
FROM #invoice_data
ORDER BY Invoiceno
	
-- Final product table (Only countable products) to be exported.
SELECT 	DISTINCT ProductCode
		, ProductName
		, p.SubCategoryID
--		, psc.SubCategory 
		, psc.CategoryID 
--		, pc.Category 
INTO #product_data		
FROM Product p
INNER JOIN ProductSubCategory psc ON psc.SubCategoryID = p.SubCategoryID 
INNER JOIN ProductCategory pc ON pc.CategoryID = psc.CategoryID 
WHERE p.PackSize = 'EA'
	
-- Subcategory table to be exported
SELECT  DISTINCT psc.SubCategoryID 
		, psc.SubCategory  
FROM ProductSubCategory psc

-- Category table to be exported.
SELECT  DISTINCT pc.CategoryID 
		, pc.Category  
FROM ProductCategory pc

DROP TABLE #product_data




GROUP BY 	id.ProductCode 
			, i.CustomerCode 
--			, i.InvoiceDate 
--HAVING (DISTINCT CustomerCode) > 3 
--WHERE (i.InvoiceDate < '2015-01-01') OR (p.PackSize != 'EA' OR id.SalesQTY > 20) 
ORDER BY CustomerCode, ProductCode  


