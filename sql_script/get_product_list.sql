DROP TABLE #ValidCustomer
DROP TABLE #ValidInvoiceNo
DROP TABLE #ExcInv
DROP TABLE #ValidInv

SELECT COUNT(*) FROM #ValidCustomer

SELECT 	i.CustomerCode
		, COUNT(DISTINCT i.InvoiceNo) AS FF
INTO #ValidCustomer
FROM Customer c
INNER JOIN Invoice i ON i.CustomerCode = c.CustomerCode 
WHERE LoyaltySettingsId = 1
GROUP BY i.CustomerCode 
HAVING COUNT(DISTINCT i.InvoiceNo) > 7


SELECT 	DISTINCT Invoiceno
INTO #ExcInv
FROM InvoiceDetails id
INNER JOIN Product p ON id.ProductCode = p.ProductCode 
WHERE p.PackSize != 'EA' OR id.SalesQTY > 20
ORDER BY Invoiceno 

SELECT COUNT(DISTINCT Invoiceno)
FROM #ExcInv

SELECT 	DISTINCT id.Invoiceno
INTO #ValidInv
FROM InvoiceDetails id 
LEFT JOIN #ExcInv e ON e.Invoiceno = id.Invoiceno 
WHERE e.Invoiceno IS NULL


SELECT 	DISTINCT i.InvoiceNo 
--		, p.PackSize 
--		, i.InvoiceDate 
INTO #ValidInvoiceNo
FROM Invoice i
INNER JOIN #ValidInv vi ON vi.Invoiceno = i.InvoiceNo 
INNER JOIN InvoiceDetails id ON i.InvoiceNo = id.Invoiceno 
INNER JOIN Product p ON p.ProductCode = id.ProductCode 
INNER JOIN #ValidCustomer vc ON vc.CustomerCode = i.CustomerCode  
--WHERE p.PackSize  = 'EA' 
GROUP BY i.InvoiceNo		
HAVING COUNT(id.ProductCode) > 2 AND COUNT(id.ProductCode) < 50 

SELECT COUNT(*)
FROM #ValidInvoiceNo

SELECT	id.Invoiceno
		, id.ProductCode
		, p.ProductName
		, id.SalesQTY 
INTO #Invoice_Sales_2
FROM InvoiceDetails id
INNER JOIN #ValidInvoiceNo i ON i.InvoiceNo = id.Invoiceno 
INNER JOIN Product p ON p.ProductCode = id.ProductCode 
WHERE  	p.PackSize = 'EA'
		AND (id.SalesQTY >= 1 AND SalesQTY < 20)
		
SELECT 	Invoiceno
		, COUNT(ProductCode)
		INTO 
FROM #Invoice_Sales
GROUP BY Invoiceno 
ORDER BY Invoiceno

SELECT *
FROM #Invoice_Sales
	ORDER BY Invoiceno	