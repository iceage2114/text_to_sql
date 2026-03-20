-- DDL export: AdventureWorks2019
-- Server : JONATHANS-PC\SQLEXPRESS
-- Tables : 72
-- Schema filter: (all)

-- ======================================================================
-- [dbo].[AWBuildVersion]
-- ======================================================================
CREATE TABLE [dbo].[AWBuildVersion] (
    [SystemInformationID] TINYINT NOT NULL,
    [Database Version] NVARCHAR(25) NOT NULL,
    [VersionDate] DATETIME NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_AWBuildVersion] PRIMARY KEY ([SystemInformationID])
);

-- ======================================================================
-- [dbo].[DatabaseLog]
-- ======================================================================
CREATE TABLE [dbo].[DatabaseLog] (
    [DatabaseLogID] INT NOT NULL,
    [PostTime] DATETIME NOT NULL,
    [DatabaseUser] NVARCHAR(128) NOT NULL,
    [Event] NVARCHAR(128) NOT NULL,
    [Schema] NVARCHAR(128) NULL,
    [Object] NVARCHAR(128) NULL,
    [TSQL] NVARCHAR(MAX) NOT NULL,
    [XmlEvent] XML NOT NULL,
    CONSTRAINT [PK_DatabaseLog] PRIMARY KEY ([DatabaseLogID])
);

-- ======================================================================
-- [dbo].[ErrorLog]
-- ======================================================================
CREATE TABLE [dbo].[ErrorLog] (
    [ErrorLogID] INT NOT NULL,
    [ErrorTime] DATETIME DEFAULT (getdate()) NOT NULL,
    [UserName] NVARCHAR(128) NOT NULL,
    [ErrorNumber] INT NOT NULL,
    [ErrorSeverity] INT NULL,
    [ErrorState] INT NULL,
    [ErrorProcedure] NVARCHAR(126) NULL,
    [ErrorLine] INT NULL,
    [ErrorMessage] NVARCHAR(4000) NOT NULL,
    CONSTRAINT [PK_ErrorLog] PRIMARY KEY ([ErrorLogID])
);

-- ======================================================================
-- [dbo].[sysdiagrams]
-- ======================================================================
CREATE TABLE [dbo].[sysdiagrams] (
    [name] NVARCHAR(128) NOT NULL,
    [principal_id] INT NOT NULL,
    [diagram_id] INT NOT NULL,
    [version] INT NULL,
    [definition] VARBINARY(MAX) NULL,
    CONSTRAINT [PK_sysdiagrams] PRIMARY KEY ([diagram_id])
);
CREATE UNIQUE INDEX [UK_principal_name]
    ON [dbo].[sysdiagrams] ([principal_id], [name]);

-- ======================================================================
-- [HumanResources].[Department]
-- ======================================================================
CREATE TABLE [HumanResources].[Department] (
    [DepartmentID] SMALLINT NOT NULL,
    [Name] NVARCHAR(50) NOT NULL,
    [GroupName] NVARCHAR(50) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_Department] PRIMARY KEY ([DepartmentID])
);
CREATE UNIQUE INDEX [AK_Department_Name]
    ON [HumanResources].[Department] ([Name]);

-- ======================================================================
-- [HumanResources].[Employee]
-- ======================================================================
CREATE TABLE [HumanResources].[Employee] (
    [BusinessEntityID] INT NOT NULL,
    [NationalIDNumber] NVARCHAR(15) NOT NULL,
    [LoginID] NVARCHAR(256) NOT NULL,
    [OrganizationNode] HIERARCHYID NULL,
    [OrganizationLevel] SMALLINT NULL,
    [JobTitle] NVARCHAR(50) NOT NULL,
    [BirthDate] DATE NOT NULL,
    [MaritalStatus] NCHAR(1) NOT NULL,
    [Gender] NCHAR(1) NOT NULL,
    [HireDate] DATE NOT NULL,
    [SalariedFlag] BIT DEFAULT ((1)) NOT NULL,
    [VacationHours] SMALLINT DEFAULT ((0)) NOT NULL,
    [SickLeaveHours] SMALLINT DEFAULT ((0)) NOT NULL,
    [CurrentFlag] BIT DEFAULT ((1)) NOT NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_Employee] PRIMARY KEY ([BusinessEntityID]),
    CONSTRAINT [FK_Employee_Person_BusinessEntityID] FOREIGN KEY ([BusinessEntityID])
        REFERENCES [Person].[Person] ([BusinessEntityID])
);
CREATE UNIQUE INDEX [AK_Employee_LoginID]
    ON [HumanResources].[Employee] ([LoginID]);
CREATE UNIQUE INDEX [AK_Employee_NationalIDNumber]
    ON [HumanResources].[Employee] ([NationalIDNumber]);
CREATE UNIQUE INDEX [AK_Employee_rowguid]
    ON [HumanResources].[Employee] ([rowguid]);
CREATE INDEX [IX_Employee_OrganizationLevel_OrganizationNode]
    ON [HumanResources].[Employee] ([OrganizationLevel], [OrganizationNode]);
CREATE INDEX [IX_Employee_OrganizationNode]
    ON [HumanResources].[Employee] ([OrganizationNode]);

-- ======================================================================
-- [HumanResources].[EmployeeDepartmentHistory]
-- ======================================================================
CREATE TABLE [HumanResources].[EmployeeDepartmentHistory] (
    [BusinessEntityID] INT NOT NULL,
    [DepartmentID] SMALLINT NOT NULL,
    [ShiftID] TINYINT NOT NULL,
    [StartDate] DATE NOT NULL,
    [EndDate] DATE NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_EmployeeDepartmentHistory] PRIMARY KEY ([BusinessEntityID], [StartDate], [DepartmentID], [ShiftID]),
    CONSTRAINT [FK_EmployeeDepartmentHistory_Department_DepartmentID] FOREIGN KEY ([DepartmentID])
        REFERENCES [HumanResources].[Department] ([DepartmentID]),
    CONSTRAINT [FK_EmployeeDepartmentHistory_Employee_BusinessEntityID] FOREIGN KEY ([BusinessEntityID])
        REFERENCES [HumanResources].[Employee] ([BusinessEntityID]),
    CONSTRAINT [FK_EmployeeDepartmentHistory_Shift_ShiftID] FOREIGN KEY ([ShiftID])
        REFERENCES [HumanResources].[Shift] ([ShiftID])
);
CREATE INDEX [IX_EmployeeDepartmentHistory_DepartmentID]
    ON [HumanResources].[EmployeeDepartmentHistory] ([DepartmentID]);
CREATE INDEX [IX_EmployeeDepartmentHistory_ShiftID]
    ON [HumanResources].[EmployeeDepartmentHistory] ([ShiftID]);

-- ======================================================================
-- [HumanResources].[EmployeePayHistory]
-- ======================================================================
CREATE TABLE [HumanResources].[EmployeePayHistory] (
    [BusinessEntityID] INT NOT NULL,
    [RateChangeDate] DATETIME NOT NULL,
    [Rate] MONEY NOT NULL,
    [PayFrequency] TINYINT NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_EmployeePayHistory] PRIMARY KEY ([BusinessEntityID], [RateChangeDate]),
    CONSTRAINT [FK_EmployeePayHistory_Employee_BusinessEntityID] FOREIGN KEY ([BusinessEntityID])
        REFERENCES [HumanResources].[Employee] ([BusinessEntityID])
);

-- ======================================================================
-- [HumanResources].[JobCandidate]
-- ======================================================================
CREATE TABLE [HumanResources].[JobCandidate] (
    [JobCandidateID] INT NOT NULL,
    [BusinessEntityID] INT NULL,
    [Resume] XML NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_JobCandidate] PRIMARY KEY ([JobCandidateID]),
    CONSTRAINT [FK_JobCandidate_Employee_BusinessEntityID] FOREIGN KEY ([BusinessEntityID])
        REFERENCES [HumanResources].[Employee] ([BusinessEntityID])
);
CREATE INDEX [IX_JobCandidate_BusinessEntityID]
    ON [HumanResources].[JobCandidate] ([BusinessEntityID]);

-- ======================================================================
-- [HumanResources].[Shift]
-- ======================================================================
CREATE TABLE [HumanResources].[Shift] (
    [ShiftID] TINYINT NOT NULL,
    [Name] NVARCHAR(50) NOT NULL,
    [StartTime] TIME NOT NULL,
    [EndTime] TIME NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_Shift] PRIMARY KEY ([ShiftID])
);
CREATE UNIQUE INDEX [AK_Shift_Name]
    ON [HumanResources].[Shift] ([Name]);
CREATE UNIQUE INDEX [AK_Shift_StartTime_EndTime]
    ON [HumanResources].[Shift] ([StartTime], [EndTime]);

-- ======================================================================
-- [Person].[Address]
-- ======================================================================
CREATE TABLE [Person].[Address] (
    [AddressID] INT NOT NULL,
    [AddressLine1] NVARCHAR(60) NOT NULL,
    [AddressLine2] NVARCHAR(60) NULL,
    [City] NVARCHAR(30) NOT NULL,
    [StateProvinceID] INT NOT NULL,
    [PostalCode] NVARCHAR(15) NOT NULL,
    [SpatialLocation] GEOGRAPHY NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_Address] PRIMARY KEY ([AddressID]),
    CONSTRAINT [FK_Address_StateProvince_StateProvinceID] FOREIGN KEY ([StateProvinceID])
        REFERENCES [Person].[StateProvince] ([StateProvinceID])
);
CREATE UNIQUE INDEX [AK_Address_rowguid]
    ON [Person].[Address] ([rowguid]);
CREATE UNIQUE INDEX [IX_Address_AddressLine1_AddressLine2_City_StateProvinceID_PostalCode]
    ON [Person].[Address] ([AddressLine1], [AddressLine2], [City], [StateProvinceID], [PostalCode]);
CREATE INDEX [IX_Address_StateProvinceID]
    ON [Person].[Address] ([StateProvinceID]);

-- ======================================================================
-- [Person].[AddressType]
-- ======================================================================
CREATE TABLE [Person].[AddressType] (
    [AddressTypeID] INT NOT NULL,
    [Name] NVARCHAR(50) NOT NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_AddressType] PRIMARY KEY ([AddressTypeID])
);
CREATE UNIQUE INDEX [AK_AddressType_Name]
    ON [Person].[AddressType] ([Name]);
CREATE UNIQUE INDEX [AK_AddressType_rowguid]
    ON [Person].[AddressType] ([rowguid]);

-- ======================================================================
-- [Person].[BusinessEntity]
-- ======================================================================
CREATE TABLE [Person].[BusinessEntity] (
    [BusinessEntityID] INT NOT NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_BusinessEntity] PRIMARY KEY ([BusinessEntityID])
);
CREATE UNIQUE INDEX [AK_BusinessEntity_rowguid]
    ON [Person].[BusinessEntity] ([rowguid]);

-- ======================================================================
-- [Person].[BusinessEntityAddress]
-- ======================================================================
CREATE TABLE [Person].[BusinessEntityAddress] (
    [BusinessEntityID] INT NOT NULL,
    [AddressID] INT NOT NULL,
    [AddressTypeID] INT NOT NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_BusinessEntityAddress] PRIMARY KEY ([BusinessEntityID], [AddressID], [AddressTypeID]),
    CONSTRAINT [FK_BusinessEntityAddress_Address_AddressID] FOREIGN KEY ([AddressID])
        REFERENCES [Person].[Address] ([AddressID]),
    CONSTRAINT [FK_BusinessEntityAddress_AddressType_AddressTypeID] FOREIGN KEY ([AddressTypeID])
        REFERENCES [Person].[AddressType] ([AddressTypeID]),
    CONSTRAINT [FK_BusinessEntityAddress_BusinessEntity_BusinessEntityID] FOREIGN KEY ([BusinessEntityID])
        REFERENCES [Person].[BusinessEntity] ([BusinessEntityID])
);
CREATE UNIQUE INDEX [AK_BusinessEntityAddress_rowguid]
    ON [Person].[BusinessEntityAddress] ([rowguid]);
CREATE INDEX [IX_BusinessEntityAddress_AddressID]
    ON [Person].[BusinessEntityAddress] ([AddressID]);
CREATE INDEX [IX_BusinessEntityAddress_AddressTypeID]
    ON [Person].[BusinessEntityAddress] ([AddressTypeID]);

-- ======================================================================
-- [Person].[BusinessEntityContact]
-- ======================================================================
CREATE TABLE [Person].[BusinessEntityContact] (
    [BusinessEntityID] INT NOT NULL,
    [PersonID] INT NOT NULL,
    [ContactTypeID] INT NOT NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_BusinessEntityContact] PRIMARY KEY ([BusinessEntityID], [PersonID], [ContactTypeID]),
    CONSTRAINT [FK_BusinessEntityContact_BusinessEntity_BusinessEntityID] FOREIGN KEY ([BusinessEntityID])
        REFERENCES [Person].[BusinessEntity] ([BusinessEntityID]),
    CONSTRAINT [FK_BusinessEntityContact_ContactType_ContactTypeID] FOREIGN KEY ([ContactTypeID])
        REFERENCES [Person].[ContactType] ([ContactTypeID]),
    CONSTRAINT [FK_BusinessEntityContact_Person_PersonID] FOREIGN KEY ([PersonID])
        REFERENCES [Person].[Person] ([BusinessEntityID])
);
CREATE UNIQUE INDEX [AK_BusinessEntityContact_rowguid]
    ON [Person].[BusinessEntityContact] ([rowguid]);
CREATE INDEX [IX_BusinessEntityContact_ContactTypeID]
    ON [Person].[BusinessEntityContact] ([ContactTypeID]);
CREATE INDEX [IX_BusinessEntityContact_PersonID]
    ON [Person].[BusinessEntityContact] ([PersonID]);

-- ======================================================================
-- [Person].[ContactType]
-- ======================================================================
CREATE TABLE [Person].[ContactType] (
    [ContactTypeID] INT NOT NULL,
    [Name] NVARCHAR(50) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_ContactType] PRIMARY KEY ([ContactTypeID])
);
CREATE UNIQUE INDEX [AK_ContactType_Name]
    ON [Person].[ContactType] ([Name]);

-- ======================================================================
-- [Person].[CountryRegion]
-- ======================================================================
CREATE TABLE [Person].[CountryRegion] (
    [CountryRegionCode] NVARCHAR(3) NOT NULL,
    [Name] NVARCHAR(50) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_CountryRegion] PRIMARY KEY ([CountryRegionCode])
);
CREATE UNIQUE INDEX [AK_CountryRegion_Name]
    ON [Person].[CountryRegion] ([Name]);

-- ======================================================================
-- [Person].[EmailAddress]
-- ======================================================================
CREATE TABLE [Person].[EmailAddress] (
    [BusinessEntityID] INT NOT NULL,
    [EmailAddressID] INT NOT NULL,
    [EmailAddress] NVARCHAR(50) NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_EmailAddress] PRIMARY KEY ([BusinessEntityID], [EmailAddressID]),
    CONSTRAINT [FK_EmailAddress_Person_BusinessEntityID] FOREIGN KEY ([BusinessEntityID])
        REFERENCES [Person].[Person] ([BusinessEntityID])
);
CREATE INDEX [IX_EmailAddress_EmailAddress]
    ON [Person].[EmailAddress] ([EmailAddress]);

-- ======================================================================
-- [Person].[Password]
-- ======================================================================
CREATE TABLE [Person].[Password] (
    [BusinessEntityID] INT NOT NULL,
    [PasswordHash] VARCHAR(128) NOT NULL,
    [PasswordSalt] VARCHAR(10) NOT NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_Password] PRIMARY KEY ([BusinessEntityID]),
    CONSTRAINT [FK_Password_Person_BusinessEntityID] FOREIGN KEY ([BusinessEntityID])
        REFERENCES [Person].[Person] ([BusinessEntityID])
);

-- ======================================================================
-- [Person].[Person]
-- ======================================================================
CREATE TABLE [Person].[Person] (
    [BusinessEntityID] INT NOT NULL,
    [PersonType] NCHAR(2) NOT NULL,
    [NameStyle] BIT DEFAULT ((0)) NOT NULL,
    [Title] NVARCHAR(8) NULL,
    [FirstName] NVARCHAR(50) NOT NULL,
    [MiddleName] NVARCHAR(50) NULL,
    [LastName] NVARCHAR(50) NOT NULL,
    [Suffix] NVARCHAR(10) NULL,
    [EmailPromotion] INT DEFAULT ((0)) NOT NULL,
    [AdditionalContactInfo] XML NULL,
    [Demographics] XML NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_Person] PRIMARY KEY ([BusinessEntityID]),
    CONSTRAINT [FK_Person_BusinessEntity_BusinessEntityID] FOREIGN KEY ([BusinessEntityID])
        REFERENCES [Person].[BusinessEntity] ([BusinessEntityID])
);
CREATE UNIQUE INDEX [AK_Person_rowguid]
    ON [Person].[Person] ([rowguid]);
CREATE INDEX [IX_Person_LastName_FirstName_MiddleName]
    ON [Person].[Person] ([LastName], [FirstName], [MiddleName]);
CREATE INDEX [PXML_Person_AddContact]
    ON [Person].[Person] ([AdditionalContactInfo]);
CREATE INDEX [PXML_Person_Demographics]
    ON [Person].[Person] ([Demographics]);
CREATE INDEX [XMLPATH_Person_Demographics]
    ON [Person].[Person] ([Demographics]);
CREATE INDEX [XMLPROPERTY_Person_Demographics]
    ON [Person].[Person] ([Demographics]);
CREATE INDEX [XMLVALUE_Person_Demographics]
    ON [Person].[Person] ([Demographics]);

-- ======================================================================
-- [Person].[PersonPhone]
-- ======================================================================
CREATE TABLE [Person].[PersonPhone] (
    [BusinessEntityID] INT NOT NULL,
    [PhoneNumber] NVARCHAR(25) NOT NULL,
    [PhoneNumberTypeID] INT NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_PersonPhone] PRIMARY KEY ([BusinessEntityID], [PhoneNumber], [PhoneNumberTypeID]),
    CONSTRAINT [FK_PersonPhone_Person_BusinessEntityID] FOREIGN KEY ([BusinessEntityID])
        REFERENCES [Person].[Person] ([BusinessEntityID]),
    CONSTRAINT [FK_PersonPhone_PhoneNumberType_PhoneNumberTypeID] FOREIGN KEY ([PhoneNumberTypeID])
        REFERENCES [Person].[PhoneNumberType] ([PhoneNumberTypeID])
);
CREATE INDEX [IX_PersonPhone_PhoneNumber]
    ON [Person].[PersonPhone] ([PhoneNumber]);

-- ======================================================================
-- [Person].[PhoneNumberType]
-- ======================================================================
CREATE TABLE [Person].[PhoneNumberType] (
    [PhoneNumberTypeID] INT NOT NULL,
    [Name] NVARCHAR(50) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_PhoneNumberType] PRIMARY KEY ([PhoneNumberTypeID])
);

-- ======================================================================
-- [Person].[StateProvince]
-- ======================================================================
CREATE TABLE [Person].[StateProvince] (
    [StateProvinceID] INT NOT NULL,
    [StateProvinceCode] NCHAR(3) NOT NULL,
    [CountryRegionCode] NVARCHAR(3) NOT NULL,
    [IsOnlyStateProvinceFlag] BIT DEFAULT ((1)) NOT NULL,
    [Name] NVARCHAR(50) NOT NULL,
    [TerritoryID] INT NOT NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_StateProvince] PRIMARY KEY ([StateProvinceID]),
    CONSTRAINT [FK_StateProvince_CountryRegion_CountryRegionCode] FOREIGN KEY ([CountryRegionCode])
        REFERENCES [Person].[CountryRegion] ([CountryRegionCode]),
    CONSTRAINT [FK_StateProvince_SalesTerritory_TerritoryID] FOREIGN KEY ([TerritoryID])
        REFERENCES [Sales].[SalesTerritory] ([TerritoryID])
);
CREATE UNIQUE INDEX [AK_StateProvince_Name]
    ON [Person].[StateProvince] ([Name]);
CREATE UNIQUE INDEX [AK_StateProvince_rowguid]
    ON [Person].[StateProvince] ([rowguid]);
CREATE UNIQUE INDEX [AK_StateProvince_StateProvinceCode_CountryRegionCode]
    ON [Person].[StateProvince] ([StateProvinceCode], [CountryRegionCode]);

-- ======================================================================
-- [Production].[BillOfMaterials]
-- ======================================================================
CREATE TABLE [Production].[BillOfMaterials] (
    [BillOfMaterialsID] INT NOT NULL,
    [ProductAssemblyID] INT NULL,
    [ComponentID] INT NOT NULL,
    [StartDate] DATETIME DEFAULT (getdate()) NOT NULL,
    [EndDate] DATETIME NULL,
    [UnitMeasureCode] NCHAR(3) NOT NULL,
    [BOMLevel] SMALLINT NOT NULL,
    [PerAssemblyQty] DECIMAL(8,2) DEFAULT ((1.00)) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_BillOfMaterials] PRIMARY KEY ([BillOfMaterialsID]),
    CONSTRAINT [FK_BillOfMaterials_Product_ComponentID] FOREIGN KEY ([ComponentID])
        REFERENCES [Production].[Product] ([ProductID]),
    CONSTRAINT [FK_BillOfMaterials_Product_ProductAssemblyID] FOREIGN KEY ([ProductAssemblyID])
        REFERENCES [Production].[Product] ([ProductID]),
    CONSTRAINT [FK_BillOfMaterials_UnitMeasure_UnitMeasureCode] FOREIGN KEY ([UnitMeasureCode])
        REFERENCES [Production].[UnitMeasure] ([UnitMeasureCode])
);
CREATE UNIQUE INDEX [AK_BillOfMaterials_ProductAssemblyID_ComponentID_StartDate]
    ON [Production].[BillOfMaterials] ([ProductAssemblyID], [ComponentID], [StartDate]);
CREATE INDEX [IX_BillOfMaterials_UnitMeasureCode]
    ON [Production].[BillOfMaterials] ([UnitMeasureCode]);

-- ======================================================================
-- [Production].[Culture]
-- ======================================================================
CREATE TABLE [Production].[Culture] (
    [CultureID] NCHAR(6) NOT NULL,
    [Name] NVARCHAR(50) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_Culture] PRIMARY KEY ([CultureID])
);
CREATE UNIQUE INDEX [AK_Culture_Name]
    ON [Production].[Culture] ([Name]);

-- ======================================================================
-- [Production].[Document]
-- ======================================================================
CREATE TABLE [Production].[Document] (
    [DocumentNode] HIERARCHYID NOT NULL,
    [DocumentLevel] SMALLINT NULL,
    [Title] NVARCHAR(50) NOT NULL,
    [Owner] INT NOT NULL,
    [FolderFlag] BIT DEFAULT ((0)) NOT NULL,
    [FileName] NVARCHAR(400) NOT NULL,
    [FileExtension] NVARCHAR(8) NOT NULL,
    [Revision] NCHAR(5) NOT NULL,
    [ChangeNumber] INT DEFAULT ((0)) NOT NULL,
    [Status] TINYINT NOT NULL,
    [DocumentSummary] NVARCHAR(MAX) NULL,
    [Document] VARBINARY(MAX) NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_Document] PRIMARY KEY ([DocumentNode]),
    CONSTRAINT [FK_Document_Employee_Owner] FOREIGN KEY ([Owner])
        REFERENCES [HumanResources].[Employee] ([BusinessEntityID])
);
CREATE UNIQUE INDEX [AK_Document_DocumentLevel_DocumentNode]
    ON [Production].[Document] ([DocumentLevel], [DocumentNode]);
CREATE UNIQUE INDEX [AK_Document_rowguid]
    ON [Production].[Document] ([rowguid]);
CREATE INDEX [IX_Document_FileName_Revision]
    ON [Production].[Document] ([FileName], [Revision]);
CREATE UNIQUE INDEX [UQ__Document__F73921F7C81C642F]
    ON [Production].[Document] ([rowguid]);

-- ======================================================================
-- [Production].[Illustration]
-- ======================================================================
CREATE TABLE [Production].[Illustration] (
    [IllustrationID] INT NOT NULL,
    [Diagram] XML NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_Illustration] PRIMARY KEY ([IllustrationID])
);

-- ======================================================================
-- [Production].[Location]
-- ======================================================================
CREATE TABLE [Production].[Location] (
    [LocationID] SMALLINT NOT NULL,
    [Name] NVARCHAR(50) NOT NULL,
    [CostRate] SMALLMONEY DEFAULT ((0.00)) NOT NULL,
    [Availability] DECIMAL(8,2) DEFAULT ((0.00)) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_Location] PRIMARY KEY ([LocationID])
);
CREATE UNIQUE INDEX [AK_Location_Name]
    ON [Production].[Location] ([Name]);

-- ======================================================================
-- [Production].[Product]
-- ======================================================================
CREATE TABLE [Production].[Product] (
    [ProductID] INT NOT NULL,
    [Name] NVARCHAR(50) NOT NULL,
    [ProductNumber] NVARCHAR(25) NOT NULL,
    [MakeFlag] BIT DEFAULT ((1)) NOT NULL,
    [FinishedGoodsFlag] BIT DEFAULT ((1)) NOT NULL,
    [Color] NVARCHAR(15) NULL,
    [SafetyStockLevel] SMALLINT NOT NULL,
    [ReorderPoint] SMALLINT NOT NULL,
    [StandardCost] MONEY NOT NULL,
    [ListPrice] MONEY NOT NULL,
    [Size] NVARCHAR(5) NULL,
    [SizeUnitMeasureCode] NCHAR(3) NULL,
    [WeightUnitMeasureCode] NCHAR(3) NULL,
    [Weight] DECIMAL(8,2) NULL,
    [DaysToManufacture] INT NOT NULL,
    [ProductLine] NCHAR(2) NULL,
    [Class] NCHAR(2) NULL,
    [Style] NCHAR(2) NULL,
    [ProductSubcategoryID] INT NULL,
    [ProductModelID] INT NULL,
    [SellStartDate] DATETIME NOT NULL,
    [SellEndDate] DATETIME NULL,
    [DiscontinuedDate] DATETIME NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_Product] PRIMARY KEY ([ProductID]),
    CONSTRAINT [FK_Product_ProductModel_ProductModelID] FOREIGN KEY ([ProductModelID])
        REFERENCES [Production].[ProductModel] ([ProductModelID]),
    CONSTRAINT [FK_Product_ProductSubcategory_ProductSubcategoryID] FOREIGN KEY ([ProductSubcategoryID])
        REFERENCES [Production].[ProductSubcategory] ([ProductSubcategoryID]),
    CONSTRAINT [FK_Product_UnitMeasure_SizeUnitMeasureCode] FOREIGN KEY ([SizeUnitMeasureCode])
        REFERENCES [Production].[UnitMeasure] ([UnitMeasureCode]),
    CONSTRAINT [FK_Product_UnitMeasure_WeightUnitMeasureCode] FOREIGN KEY ([WeightUnitMeasureCode])
        REFERENCES [Production].[UnitMeasure] ([UnitMeasureCode])
);
CREATE UNIQUE INDEX [AK_Product_Name]
    ON [Production].[Product] ([Name]);
CREATE UNIQUE INDEX [AK_Product_ProductNumber]
    ON [Production].[Product] ([ProductNumber]);
CREATE UNIQUE INDEX [AK_Product_rowguid]
    ON [Production].[Product] ([rowguid]);

-- ======================================================================
-- [Production].[ProductCategory]
-- ======================================================================
CREATE TABLE [Production].[ProductCategory] (
    [ProductCategoryID] INT NOT NULL,
    [Name] NVARCHAR(50) NOT NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_ProductCategory] PRIMARY KEY ([ProductCategoryID])
);
CREATE UNIQUE INDEX [AK_ProductCategory_Name]
    ON [Production].[ProductCategory] ([Name]);
CREATE UNIQUE INDEX [AK_ProductCategory_rowguid]
    ON [Production].[ProductCategory] ([rowguid]);

-- ======================================================================
-- [Production].[ProductCostHistory]
-- ======================================================================
CREATE TABLE [Production].[ProductCostHistory] (
    [ProductID] INT NOT NULL,
    [StartDate] DATETIME NOT NULL,
    [EndDate] DATETIME NULL,
    [StandardCost] MONEY NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_ProductCostHistory] PRIMARY KEY ([ProductID], [StartDate]),
    CONSTRAINT [FK_ProductCostHistory_Product_ProductID] FOREIGN KEY ([ProductID])
        REFERENCES [Production].[Product] ([ProductID])
);

-- ======================================================================
-- [Production].[ProductDescription]
-- ======================================================================
CREATE TABLE [Production].[ProductDescription] (
    [ProductDescriptionID] INT NOT NULL,
    [Description] NVARCHAR(400) NOT NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_ProductDescription] PRIMARY KEY ([ProductDescriptionID])
);
CREATE UNIQUE INDEX [AK_ProductDescription_rowguid]
    ON [Production].[ProductDescription] ([rowguid]);

-- ======================================================================
-- [Production].[ProductDocument]
-- ======================================================================
CREATE TABLE [Production].[ProductDocument] (
    [ProductID] INT NOT NULL,
    [DocumentNode] HIERARCHYID NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_ProductDocument] PRIMARY KEY ([ProductID], [DocumentNode]),
    CONSTRAINT [FK_ProductDocument_Document_DocumentNode] FOREIGN KEY ([DocumentNode])
        REFERENCES [Production].[Document] ([DocumentNode]),
    CONSTRAINT [FK_ProductDocument_Product_ProductID] FOREIGN KEY ([ProductID])
        REFERENCES [Production].[Product] ([ProductID])
);

-- ======================================================================
-- [Production].[ProductInventory]
-- ======================================================================
CREATE TABLE [Production].[ProductInventory] (
    [ProductID] INT NOT NULL,
    [LocationID] SMALLINT NOT NULL,
    [Shelf] NVARCHAR(10) NOT NULL,
    [Bin] TINYINT NOT NULL,
    [Quantity] SMALLINT DEFAULT ((0)) NOT NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_ProductInventory] PRIMARY KEY ([ProductID], [LocationID]),
    CONSTRAINT [FK_ProductInventory_Location_LocationID] FOREIGN KEY ([LocationID])
        REFERENCES [Production].[Location] ([LocationID]),
    CONSTRAINT [FK_ProductInventory_Product_ProductID] FOREIGN KEY ([ProductID])
        REFERENCES [Production].[Product] ([ProductID])
);

-- ======================================================================
-- [Production].[ProductListPriceHistory]
-- ======================================================================
CREATE TABLE [Production].[ProductListPriceHistory] (
    [ProductID] INT NOT NULL,
    [StartDate] DATETIME NOT NULL,
    [EndDate] DATETIME NULL,
    [ListPrice] MONEY NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_ProductListPriceHistory] PRIMARY KEY ([ProductID], [StartDate]),
    CONSTRAINT [FK_ProductListPriceHistory_Product_ProductID] FOREIGN KEY ([ProductID])
        REFERENCES [Production].[Product] ([ProductID])
);

-- ======================================================================
-- [Production].[ProductModel]
-- ======================================================================
CREATE TABLE [Production].[ProductModel] (
    [ProductModelID] INT NOT NULL,
    [Name] NVARCHAR(50) NOT NULL,
    [CatalogDescription] XML NULL,
    [Instructions] XML NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_ProductModel] PRIMARY KEY ([ProductModelID])
);
CREATE UNIQUE INDEX [AK_ProductModel_Name]
    ON [Production].[ProductModel] ([Name]);
CREATE UNIQUE INDEX [AK_ProductModel_rowguid]
    ON [Production].[ProductModel] ([rowguid]);
CREATE INDEX [PXML_ProductModel_CatalogDescription]
    ON [Production].[ProductModel] ([CatalogDescription]);
CREATE INDEX [PXML_ProductModel_Instructions]
    ON [Production].[ProductModel] ([Instructions]);

-- ======================================================================
-- [Production].[ProductModelIllustration]
-- ======================================================================
CREATE TABLE [Production].[ProductModelIllustration] (
    [ProductModelID] INT NOT NULL,
    [IllustrationID] INT NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_ProductModelIllustration] PRIMARY KEY ([ProductModelID], [IllustrationID]),
    CONSTRAINT [FK_ProductModelIllustration_Illustration_IllustrationID] FOREIGN KEY ([IllustrationID])
        REFERENCES [Production].[Illustration] ([IllustrationID]),
    CONSTRAINT [FK_ProductModelIllustration_ProductModel_ProductModelID] FOREIGN KEY ([ProductModelID])
        REFERENCES [Production].[ProductModel] ([ProductModelID])
);

-- ======================================================================
-- [Production].[ProductModelProductDescriptionCulture]
-- ======================================================================
CREATE TABLE [Production].[ProductModelProductDescriptionCulture] (
    [ProductModelID] INT NOT NULL,
    [ProductDescriptionID] INT NOT NULL,
    [CultureID] NCHAR(6) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_ProductModelProductDescriptionCulture] PRIMARY KEY ([ProductModelID], [ProductDescriptionID], [CultureID]),
    CONSTRAINT [FK_ProductModelProductDescriptionCulture_Culture_CultureID] FOREIGN KEY ([CultureID])
        REFERENCES [Production].[Culture] ([CultureID]),
    CONSTRAINT [FK_ProductModelProductDescriptionCulture_ProductDescription_ProductDescriptionID] FOREIGN KEY ([ProductDescriptionID])
        REFERENCES [Production].[ProductDescription] ([ProductDescriptionID]),
    CONSTRAINT [FK_ProductModelProductDescriptionCulture_ProductModel_ProductModelID] FOREIGN KEY ([ProductModelID])
        REFERENCES [Production].[ProductModel] ([ProductModelID])
);

-- ======================================================================
-- [Production].[ProductPhoto]
-- ======================================================================
CREATE TABLE [Production].[ProductPhoto] (
    [ProductPhotoID] INT NOT NULL,
    [ThumbNailPhoto] VARBINARY(MAX) NULL,
    [ThumbnailPhotoFileName] NVARCHAR(50) NULL,
    [LargePhoto] VARBINARY(MAX) NULL,
    [LargePhotoFileName] NVARCHAR(50) NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_ProductPhoto] PRIMARY KEY ([ProductPhotoID])
);

-- ======================================================================
-- [Production].[ProductProductPhoto]
-- ======================================================================
CREATE TABLE [Production].[ProductProductPhoto] (
    [ProductID] INT NOT NULL,
    [ProductPhotoID] INT NOT NULL,
    [Primary] BIT DEFAULT ((0)) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_ProductProductPhoto] PRIMARY KEY ([ProductID], [ProductPhotoID]),
    CONSTRAINT [FK_ProductProductPhoto_Product_ProductID] FOREIGN KEY ([ProductID])
        REFERENCES [Production].[Product] ([ProductID]),
    CONSTRAINT [FK_ProductProductPhoto_ProductPhoto_ProductPhotoID] FOREIGN KEY ([ProductPhotoID])
        REFERENCES [Production].[ProductPhoto] ([ProductPhotoID])
);

-- ======================================================================
-- [Production].[ProductReview]
-- ======================================================================
CREATE TABLE [Production].[ProductReview] (
    [ProductReviewID] INT NOT NULL,
    [ProductID] INT NOT NULL,
    [ReviewerName] NVARCHAR(50) NOT NULL,
    [ReviewDate] DATETIME DEFAULT (getdate()) NOT NULL,
    [EmailAddress] NVARCHAR(50) NOT NULL,
    [Rating] INT NOT NULL,
    [Comments] NVARCHAR(3850) NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_ProductReview] PRIMARY KEY ([ProductReviewID]),
    CONSTRAINT [FK_ProductReview_Product_ProductID] FOREIGN KEY ([ProductID])
        REFERENCES [Production].[Product] ([ProductID])
);
CREATE INDEX [IX_ProductReview_ProductID_Name]
    ON [Production].[ProductReview] ([Comments], [ProductID], [ReviewerName]);

-- ======================================================================
-- [Production].[ProductSubcategory]
-- ======================================================================
CREATE TABLE [Production].[ProductSubcategory] (
    [ProductSubcategoryID] INT NOT NULL,
    [ProductCategoryID] INT NOT NULL,
    [Name] NVARCHAR(50) NOT NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_ProductSubcategory] PRIMARY KEY ([ProductSubcategoryID]),
    CONSTRAINT [FK_ProductSubcategory_ProductCategory_ProductCategoryID] FOREIGN KEY ([ProductCategoryID])
        REFERENCES [Production].[ProductCategory] ([ProductCategoryID])
);
CREATE UNIQUE INDEX [AK_ProductSubcategory_Name]
    ON [Production].[ProductSubcategory] ([Name]);
CREATE UNIQUE INDEX [AK_ProductSubcategory_rowguid]
    ON [Production].[ProductSubcategory] ([rowguid]);

-- ======================================================================
-- [Production].[ScrapReason]
-- ======================================================================
CREATE TABLE [Production].[ScrapReason] (
    [ScrapReasonID] SMALLINT NOT NULL,
    [Name] NVARCHAR(50) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_ScrapReason] PRIMARY KEY ([ScrapReasonID])
);
CREATE UNIQUE INDEX [AK_ScrapReason_Name]
    ON [Production].[ScrapReason] ([Name]);

-- ======================================================================
-- [Production].[TransactionHistory]
-- ======================================================================
CREATE TABLE [Production].[TransactionHistory] (
    [TransactionID] INT NOT NULL,
    [ProductID] INT NOT NULL,
    [ReferenceOrderID] INT NOT NULL,
    [ReferenceOrderLineID] INT DEFAULT ((0)) NOT NULL,
    [TransactionDate] DATETIME DEFAULT (getdate()) NOT NULL,
    [TransactionType] NCHAR(1) NOT NULL,
    [Quantity] INT NOT NULL,
    [ActualCost] MONEY NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_TransactionHistory] PRIMARY KEY ([TransactionID]),
    CONSTRAINT [FK_TransactionHistory_Product_ProductID] FOREIGN KEY ([ProductID])
        REFERENCES [Production].[Product] ([ProductID])
);
CREATE INDEX [IX_TransactionHistory_ProductID]
    ON [Production].[TransactionHistory] ([ProductID]);
CREATE INDEX [IX_TransactionHistory_ReferenceOrderID_ReferenceOrderLineID]
    ON [Production].[TransactionHistory] ([ReferenceOrderID], [ReferenceOrderLineID]);

-- ======================================================================
-- [Production].[TransactionHistoryArchive]
-- ======================================================================
CREATE TABLE [Production].[TransactionHistoryArchive] (
    [TransactionID] INT NOT NULL,
    [ProductID] INT NOT NULL,
    [ReferenceOrderID] INT NOT NULL,
    [ReferenceOrderLineID] INT DEFAULT ((0)) NOT NULL,
    [TransactionDate] DATETIME DEFAULT (getdate()) NOT NULL,
    [TransactionType] NCHAR(1) NOT NULL,
    [Quantity] INT NOT NULL,
    [ActualCost] MONEY NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_TransactionHistoryArchive] PRIMARY KEY ([TransactionID])
);
CREATE INDEX [IX_TransactionHistoryArchive_ProductID]
    ON [Production].[TransactionHistoryArchive] ([ProductID]);
CREATE INDEX [IX_TransactionHistoryArchive_ReferenceOrderID_ReferenceOrderLineID]
    ON [Production].[TransactionHistoryArchive] ([ReferenceOrderID], [ReferenceOrderLineID]);

-- ======================================================================
-- [Production].[UnitMeasure]
-- ======================================================================
CREATE TABLE [Production].[UnitMeasure] (
    [UnitMeasureCode] NCHAR(3) NOT NULL,
    [Name] NVARCHAR(50) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_UnitMeasure] PRIMARY KEY ([UnitMeasureCode])
);
CREATE UNIQUE INDEX [AK_UnitMeasure_Name]
    ON [Production].[UnitMeasure] ([Name]);

-- ======================================================================
-- [Production].[WorkOrder]
-- ======================================================================
CREATE TABLE [Production].[WorkOrder] (
    [WorkOrderID] INT NOT NULL,
    [ProductID] INT NOT NULL,
    [OrderQty] INT NOT NULL,
    [StockedQty] INT NOT NULL,
    [ScrappedQty] SMALLINT NOT NULL,
    [StartDate] DATETIME NOT NULL,
    [EndDate] DATETIME NULL,
    [DueDate] DATETIME NOT NULL,
    [ScrapReasonID] SMALLINT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_WorkOrder] PRIMARY KEY ([WorkOrderID]),
    CONSTRAINT [FK_WorkOrder_Product_ProductID] FOREIGN KEY ([ProductID])
        REFERENCES [Production].[Product] ([ProductID]),
    CONSTRAINT [FK_WorkOrder_ScrapReason_ScrapReasonID] FOREIGN KEY ([ScrapReasonID])
        REFERENCES [Production].[ScrapReason] ([ScrapReasonID])
);
CREATE INDEX [IX_WorkOrder_ProductID]
    ON [Production].[WorkOrder] ([ProductID]);
CREATE INDEX [IX_WorkOrder_ScrapReasonID]
    ON [Production].[WorkOrder] ([ScrapReasonID]);

-- ======================================================================
-- [Production].[WorkOrderRouting]
-- ======================================================================
CREATE TABLE [Production].[WorkOrderRouting] (
    [WorkOrderID] INT NOT NULL,
    [ProductID] INT NOT NULL,
    [OperationSequence] SMALLINT NOT NULL,
    [LocationID] SMALLINT NOT NULL,
    [ScheduledStartDate] DATETIME NOT NULL,
    [ScheduledEndDate] DATETIME NOT NULL,
    [ActualStartDate] DATETIME NULL,
    [ActualEndDate] DATETIME NULL,
    [ActualResourceHrs] DECIMAL(9,4) NULL,
    [PlannedCost] MONEY NOT NULL,
    [ActualCost] MONEY NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_WorkOrderRouting] PRIMARY KEY ([WorkOrderID], [ProductID], [OperationSequence]),
    CONSTRAINT [FK_WorkOrderRouting_Location_LocationID] FOREIGN KEY ([LocationID])
        REFERENCES [Production].[Location] ([LocationID]),
    CONSTRAINT [FK_WorkOrderRouting_WorkOrder_WorkOrderID] FOREIGN KEY ([WorkOrderID])
        REFERENCES [Production].[WorkOrder] ([WorkOrderID])
);
CREATE INDEX [IX_WorkOrderRouting_ProductID]
    ON [Production].[WorkOrderRouting] ([ProductID]);

-- ======================================================================
-- [Purchasing].[ProductVendor]
-- ======================================================================
CREATE TABLE [Purchasing].[ProductVendor] (
    [ProductID] INT NOT NULL,
    [BusinessEntityID] INT NOT NULL,
    [AverageLeadTime] INT NOT NULL,
    [StandardPrice] MONEY NOT NULL,
    [LastReceiptCost] MONEY NULL,
    [LastReceiptDate] DATETIME NULL,
    [MinOrderQty] INT NOT NULL,
    [MaxOrderQty] INT NOT NULL,
    [OnOrderQty] INT NULL,
    [UnitMeasureCode] NCHAR(3) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_ProductVendor] PRIMARY KEY ([ProductID], [BusinessEntityID]),
    CONSTRAINT [FK_ProductVendor_Product_ProductID] FOREIGN KEY ([ProductID])
        REFERENCES [Production].[Product] ([ProductID]),
    CONSTRAINT [FK_ProductVendor_UnitMeasure_UnitMeasureCode] FOREIGN KEY ([UnitMeasureCode])
        REFERENCES [Production].[UnitMeasure] ([UnitMeasureCode]),
    CONSTRAINT [FK_ProductVendor_Vendor_BusinessEntityID] FOREIGN KEY ([BusinessEntityID])
        REFERENCES [Purchasing].[Vendor] ([BusinessEntityID])
);
CREATE INDEX [IX_ProductVendor_BusinessEntityID]
    ON [Purchasing].[ProductVendor] ([BusinessEntityID]);
CREATE INDEX [IX_ProductVendor_UnitMeasureCode]
    ON [Purchasing].[ProductVendor] ([UnitMeasureCode]);

-- ======================================================================
-- [Purchasing].[PurchaseOrderDetail]
-- ======================================================================
CREATE TABLE [Purchasing].[PurchaseOrderDetail] (
    [PurchaseOrderID] INT NOT NULL,
    [PurchaseOrderDetailID] INT NOT NULL,
    [DueDate] DATETIME NOT NULL,
    [OrderQty] SMALLINT NOT NULL,
    [ProductID] INT NOT NULL,
    [UnitPrice] MONEY NOT NULL,
    [LineTotal] MONEY NOT NULL,
    [ReceivedQty] DECIMAL(8,2) NOT NULL,
    [RejectedQty] DECIMAL(8,2) NOT NULL,
    [StockedQty] DECIMAL(9,2) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_PurchaseOrderDetail] PRIMARY KEY ([PurchaseOrderID], [PurchaseOrderDetailID]),
    CONSTRAINT [FK_PurchaseOrderDetail_Product_ProductID] FOREIGN KEY ([ProductID])
        REFERENCES [Production].[Product] ([ProductID]),
    CONSTRAINT [FK_PurchaseOrderDetail_PurchaseOrderHeader_PurchaseOrderID] FOREIGN KEY ([PurchaseOrderID])
        REFERENCES [Purchasing].[PurchaseOrderHeader] ([PurchaseOrderID])
);
CREATE INDEX [IX_PurchaseOrderDetail_ProductID]
    ON [Purchasing].[PurchaseOrderDetail] ([ProductID]);

-- ======================================================================
-- [Purchasing].[PurchaseOrderHeader]
-- ======================================================================
CREATE TABLE [Purchasing].[PurchaseOrderHeader] (
    [PurchaseOrderID] INT NOT NULL,
    [RevisionNumber] TINYINT DEFAULT ((0)) NOT NULL,
    [Status] TINYINT DEFAULT ((1)) NOT NULL,
    [EmployeeID] INT NOT NULL,
    [VendorID] INT NOT NULL,
    [ShipMethodID] INT NOT NULL,
    [OrderDate] DATETIME DEFAULT (getdate()) NOT NULL,
    [ShipDate] DATETIME NULL,
    [SubTotal] MONEY DEFAULT ((0.00)) NOT NULL,
    [TaxAmt] MONEY DEFAULT ((0.00)) NOT NULL,
    [Freight] MONEY DEFAULT ((0.00)) NOT NULL,
    [TotalDue] MONEY NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_PurchaseOrderHeader] PRIMARY KEY ([PurchaseOrderID]),
    CONSTRAINT [FK_PurchaseOrderHeader_Employee_EmployeeID] FOREIGN KEY ([EmployeeID])
        REFERENCES [HumanResources].[Employee] ([BusinessEntityID]),
    CONSTRAINT [FK_PurchaseOrderHeader_ShipMethod_ShipMethodID] FOREIGN KEY ([ShipMethodID])
        REFERENCES [Purchasing].[ShipMethod] ([ShipMethodID]),
    CONSTRAINT [FK_PurchaseOrderHeader_Vendor_VendorID] FOREIGN KEY ([VendorID])
        REFERENCES [Purchasing].[Vendor] ([BusinessEntityID])
);
CREATE INDEX [IX_PurchaseOrderHeader_EmployeeID]
    ON [Purchasing].[PurchaseOrderHeader] ([EmployeeID]);
CREATE INDEX [IX_PurchaseOrderHeader_VendorID]
    ON [Purchasing].[PurchaseOrderHeader] ([VendorID]);

-- ======================================================================
-- [Purchasing].[ShipMethod]
-- ======================================================================
CREATE TABLE [Purchasing].[ShipMethod] (
    [ShipMethodID] INT NOT NULL,
    [Name] NVARCHAR(50) NOT NULL,
    [ShipBase] MONEY DEFAULT ((0.00)) NOT NULL,
    [ShipRate] MONEY DEFAULT ((0.00)) NOT NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_ShipMethod] PRIMARY KEY ([ShipMethodID])
);
CREATE UNIQUE INDEX [AK_ShipMethod_Name]
    ON [Purchasing].[ShipMethod] ([Name]);
CREATE UNIQUE INDEX [AK_ShipMethod_rowguid]
    ON [Purchasing].[ShipMethod] ([rowguid]);

-- ======================================================================
-- [Purchasing].[Vendor]
-- ======================================================================
CREATE TABLE [Purchasing].[Vendor] (
    [BusinessEntityID] INT NOT NULL,
    [AccountNumber] NVARCHAR(15) NOT NULL,
    [Name] NVARCHAR(50) NOT NULL,
    [CreditRating] TINYINT NOT NULL,
    [PreferredVendorStatus] BIT DEFAULT ((1)) NOT NULL,
    [ActiveFlag] BIT DEFAULT ((1)) NOT NULL,
    [PurchasingWebServiceURL] NVARCHAR(1024) NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_Vendor] PRIMARY KEY ([BusinessEntityID]),
    CONSTRAINT [FK_Vendor_BusinessEntity_BusinessEntityID] FOREIGN KEY ([BusinessEntityID])
        REFERENCES [Person].[BusinessEntity] ([BusinessEntityID])
);
CREATE UNIQUE INDEX [AK_Vendor_AccountNumber]
    ON [Purchasing].[Vendor] ([AccountNumber]);

-- ======================================================================
-- [Sales].[CountryRegionCurrency]
-- ======================================================================
CREATE TABLE [Sales].[CountryRegionCurrency] (
    [CountryRegionCode] NVARCHAR(3) NOT NULL,
    [CurrencyCode] NCHAR(3) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_CountryRegionCurrency] PRIMARY KEY ([CountryRegionCode], [CurrencyCode]),
    CONSTRAINT [FK_CountryRegionCurrency_CountryRegion_CountryRegionCode] FOREIGN KEY ([CountryRegionCode])
        REFERENCES [Person].[CountryRegion] ([CountryRegionCode]),
    CONSTRAINT [FK_CountryRegionCurrency_Currency_CurrencyCode] FOREIGN KEY ([CurrencyCode])
        REFERENCES [Sales].[Currency] ([CurrencyCode])
);
CREATE INDEX [IX_CountryRegionCurrency_CurrencyCode]
    ON [Sales].[CountryRegionCurrency] ([CurrencyCode]);

-- ======================================================================
-- [Sales].[CreditCard]
-- ======================================================================
CREATE TABLE [Sales].[CreditCard] (
    [CreditCardID] INT NOT NULL,
    [CardType] NVARCHAR(50) NOT NULL,
    [CardNumber] NVARCHAR(25) NOT NULL,
    [ExpMonth] TINYINT NOT NULL,
    [ExpYear] SMALLINT NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_CreditCard] PRIMARY KEY ([CreditCardID])
);
CREATE UNIQUE INDEX [AK_CreditCard_CardNumber]
    ON [Sales].[CreditCard] ([CardNumber]);

-- ======================================================================
-- [Sales].[Currency]
-- ======================================================================
CREATE TABLE [Sales].[Currency] (
    [CurrencyCode] NCHAR(3) NOT NULL,
    [Name] NVARCHAR(50) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_Currency] PRIMARY KEY ([CurrencyCode])
);
CREATE UNIQUE INDEX [AK_Currency_Name]
    ON [Sales].[Currency] ([Name]);

-- ======================================================================
-- [Sales].[CurrencyRate]
-- ======================================================================
CREATE TABLE [Sales].[CurrencyRate] (
    [CurrencyRateID] INT NOT NULL,
    [CurrencyRateDate] DATETIME NOT NULL,
    [FromCurrencyCode] NCHAR(3) NOT NULL,
    [ToCurrencyCode] NCHAR(3) NOT NULL,
    [AverageRate] MONEY NOT NULL,
    [EndOfDayRate] MONEY NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_CurrencyRate] PRIMARY KEY ([CurrencyRateID]),
    CONSTRAINT [FK_CurrencyRate_Currency_FromCurrencyCode] FOREIGN KEY ([FromCurrencyCode])
        REFERENCES [Sales].[Currency] ([CurrencyCode]),
    CONSTRAINT [FK_CurrencyRate_Currency_ToCurrencyCode] FOREIGN KEY ([ToCurrencyCode])
        REFERENCES [Sales].[Currency] ([CurrencyCode])
);
CREATE UNIQUE INDEX [AK_CurrencyRate_CurrencyRateDate_FromCurrencyCode_ToCurrencyCode]
    ON [Sales].[CurrencyRate] ([CurrencyRateDate], [FromCurrencyCode], [ToCurrencyCode]);

-- ======================================================================
-- [Sales].[Customer]
-- ======================================================================
CREATE TABLE [Sales].[Customer] (
    [CustomerID] INT NOT NULL,
    [PersonID] INT NULL,
    [StoreID] INT NULL,
    [TerritoryID] INT NULL,
    [AccountNumber] VARCHAR(10) NOT NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_Customer] PRIMARY KEY ([CustomerID]),
    CONSTRAINT [FK_Customer_Person_PersonID] FOREIGN KEY ([PersonID])
        REFERENCES [Person].[Person] ([BusinessEntityID]),
    CONSTRAINT [FK_Customer_SalesTerritory_TerritoryID] FOREIGN KEY ([TerritoryID])
        REFERENCES [Sales].[SalesTerritory] ([TerritoryID]),
    CONSTRAINT [FK_Customer_Store_StoreID] FOREIGN KEY ([StoreID])
        REFERENCES [Sales].[Store] ([BusinessEntityID])
);
CREATE UNIQUE INDEX [AK_Customer_AccountNumber]
    ON [Sales].[Customer] ([AccountNumber]);
CREATE UNIQUE INDEX [AK_Customer_rowguid]
    ON [Sales].[Customer] ([rowguid]);
CREATE INDEX [IX_Customer_TerritoryID]
    ON [Sales].[Customer] ([TerritoryID]);

-- ======================================================================
-- [Sales].[PersonCreditCard]
-- ======================================================================
CREATE TABLE [Sales].[PersonCreditCard] (
    [BusinessEntityID] INT NOT NULL,
    [CreditCardID] INT NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_PersonCreditCard] PRIMARY KEY ([BusinessEntityID], [CreditCardID]),
    CONSTRAINT [FK_PersonCreditCard_CreditCard_CreditCardID] FOREIGN KEY ([CreditCardID])
        REFERENCES [Sales].[CreditCard] ([CreditCardID]),
    CONSTRAINT [FK_PersonCreditCard_Person_BusinessEntityID] FOREIGN KEY ([BusinessEntityID])
        REFERENCES [Person].[Person] ([BusinessEntityID])
);

-- ======================================================================
-- [Sales].[SalesOrderDetail]
-- ======================================================================
CREATE TABLE [Sales].[SalesOrderDetail] (
    [SalesOrderID] INT NOT NULL,
    [SalesOrderDetailID] INT NOT NULL,
    [CarrierTrackingNumber] NVARCHAR(25) NULL,
    [OrderQty] SMALLINT NOT NULL,
    [ProductID] INT NOT NULL,
    [SpecialOfferID] INT NOT NULL,
    [UnitPrice] MONEY NOT NULL,
    [UnitPriceDiscount] MONEY DEFAULT ((0.0)) NOT NULL,
    [LineTotal] NUMERIC(38,6) NOT NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_SalesOrderDetail] PRIMARY KEY ([SalesOrderID], [SalesOrderDetailID]),
    CONSTRAINT [FK_SalesOrderDetail_SalesOrderHeader_SalesOrderID] FOREIGN KEY ([SalesOrderID])
        REFERENCES [Sales].[SalesOrderHeader] ([SalesOrderID]),
    CONSTRAINT [FK_SalesOrderDetail_SpecialOfferProduct_SpecialOfferIDProductID] FOREIGN KEY ([SpecialOfferID], [ProductID])
        REFERENCES [Sales].[SpecialOfferProduct] ([SpecialOfferID], [ProductID])
);
CREATE UNIQUE INDEX [AK_SalesOrderDetail_rowguid]
    ON [Sales].[SalesOrderDetail] ([rowguid]);
CREATE INDEX [IX_SalesOrderDetail_ProductID]
    ON [Sales].[SalesOrderDetail] ([ProductID]);

-- ======================================================================
-- [Sales].[SalesOrderHeader]
-- ======================================================================
CREATE TABLE [Sales].[SalesOrderHeader] (
    [SalesOrderID] INT NOT NULL,
    [RevisionNumber] TINYINT DEFAULT ((0)) NOT NULL,
    [OrderDate] DATETIME DEFAULT (getdate()) NOT NULL,
    [DueDate] DATETIME NOT NULL,
    [ShipDate] DATETIME NULL,
    [Status] TINYINT DEFAULT ((1)) NOT NULL,
    [OnlineOrderFlag] BIT DEFAULT ((1)) NOT NULL,
    [SalesOrderNumber] NVARCHAR(25) NOT NULL,
    [PurchaseOrderNumber] NVARCHAR(25) NULL,
    [AccountNumber] NVARCHAR(15) NULL,
    [CustomerID] INT NOT NULL,
    [SalesPersonID] INT NULL,
    [TerritoryID] INT NULL,
    [BillToAddressID] INT NOT NULL,
    [ShipToAddressID] INT NOT NULL,
    [ShipMethodID] INT NOT NULL,
    [CreditCardID] INT NULL,
    [CreditCardApprovalCode] VARCHAR(15) NULL,
    [CurrencyRateID] INT NULL,
    [SubTotal] MONEY DEFAULT ((0.00)) NOT NULL,
    [TaxAmt] MONEY DEFAULT ((0.00)) NOT NULL,
    [Freight] MONEY DEFAULT ((0.00)) NOT NULL,
    [TotalDue] MONEY NOT NULL,
    [Comment] NVARCHAR(128) NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_SalesOrderHeader] PRIMARY KEY ([SalesOrderID]),
    CONSTRAINT [FK_SalesOrderHeader_Address_BillToAddressID] FOREIGN KEY ([BillToAddressID])
        REFERENCES [Person].[Address] ([AddressID]),
    CONSTRAINT [FK_SalesOrderHeader_Address_ShipToAddressID] FOREIGN KEY ([ShipToAddressID])
        REFERENCES [Person].[Address] ([AddressID]),
    CONSTRAINT [FK_SalesOrderHeader_CreditCard_CreditCardID] FOREIGN KEY ([CreditCardID])
        REFERENCES [Sales].[CreditCard] ([CreditCardID]),
    CONSTRAINT [FK_SalesOrderHeader_CurrencyRate_CurrencyRateID] FOREIGN KEY ([CurrencyRateID])
        REFERENCES [Sales].[CurrencyRate] ([CurrencyRateID]),
    CONSTRAINT [FK_SalesOrderHeader_Customer_CustomerID] FOREIGN KEY ([CustomerID])
        REFERENCES [Sales].[Customer] ([CustomerID]),
    CONSTRAINT [FK_SalesOrderHeader_SalesPerson_SalesPersonID] FOREIGN KEY ([SalesPersonID])
        REFERENCES [Sales].[SalesPerson] ([BusinessEntityID]),
    CONSTRAINT [FK_SalesOrderHeader_SalesTerritory_TerritoryID] FOREIGN KEY ([TerritoryID])
        REFERENCES [Sales].[SalesTerritory] ([TerritoryID]),
    CONSTRAINT [FK_SalesOrderHeader_ShipMethod_ShipMethodID] FOREIGN KEY ([ShipMethodID])
        REFERENCES [Purchasing].[ShipMethod] ([ShipMethodID])
);
CREATE UNIQUE INDEX [AK_SalesOrderHeader_rowguid]
    ON [Sales].[SalesOrderHeader] ([rowguid]);
CREATE UNIQUE INDEX [AK_SalesOrderHeader_SalesOrderNumber]
    ON [Sales].[SalesOrderHeader] ([SalesOrderNumber]);
CREATE INDEX [IX_SalesOrderHeader_CustomerID]
    ON [Sales].[SalesOrderHeader] ([CustomerID]);
CREATE INDEX [IX_SalesOrderHeader_SalesPersonID]
    ON [Sales].[SalesOrderHeader] ([SalesPersonID]);

-- ======================================================================
-- [Sales].[SalesOrderHeaderSalesReason]
-- ======================================================================
CREATE TABLE [Sales].[SalesOrderHeaderSalesReason] (
    [SalesOrderID] INT NOT NULL,
    [SalesReasonID] INT NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_SalesOrderHeaderSalesReason] PRIMARY KEY ([SalesOrderID], [SalesReasonID]),
    CONSTRAINT [FK_SalesOrderHeaderSalesReason_SalesOrderHeader_SalesOrderID] FOREIGN KEY ([SalesOrderID])
        REFERENCES [Sales].[SalesOrderHeader] ([SalesOrderID]),
    CONSTRAINT [FK_SalesOrderHeaderSalesReason_SalesReason_SalesReasonID] FOREIGN KEY ([SalesReasonID])
        REFERENCES [Sales].[SalesReason] ([SalesReasonID])
);

-- ======================================================================
-- [Sales].[SalesPerson]
-- ======================================================================
CREATE TABLE [Sales].[SalesPerson] (
    [BusinessEntityID] INT NOT NULL,
    [TerritoryID] INT NULL,
    [SalesQuota] MONEY NULL,
    [Bonus] MONEY DEFAULT ((0.00)) NOT NULL,
    [CommissionPct] SMALLMONEY DEFAULT ((0.00)) NOT NULL,
    [SalesYTD] MONEY DEFAULT ((0.00)) NOT NULL,
    [SalesLastYear] MONEY DEFAULT ((0.00)) NOT NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_SalesPerson] PRIMARY KEY ([BusinessEntityID]),
    CONSTRAINT [FK_SalesPerson_Employee_BusinessEntityID] FOREIGN KEY ([BusinessEntityID])
        REFERENCES [HumanResources].[Employee] ([BusinessEntityID]),
    CONSTRAINT [FK_SalesPerson_SalesTerritory_TerritoryID] FOREIGN KEY ([TerritoryID])
        REFERENCES [Sales].[SalesTerritory] ([TerritoryID])
);
CREATE UNIQUE INDEX [AK_SalesPerson_rowguid]
    ON [Sales].[SalesPerson] ([rowguid]);

-- ======================================================================
-- [Sales].[SalesPersonQuotaHistory]
-- ======================================================================
CREATE TABLE [Sales].[SalesPersonQuotaHistory] (
    [BusinessEntityID] INT NOT NULL,
    [QuotaDate] DATETIME NOT NULL,
    [SalesQuota] MONEY NOT NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_SalesPersonQuotaHistory] PRIMARY KEY ([BusinessEntityID], [QuotaDate]),
    CONSTRAINT [FK_SalesPersonQuotaHistory_SalesPerson_BusinessEntityID] FOREIGN KEY ([BusinessEntityID])
        REFERENCES [Sales].[SalesPerson] ([BusinessEntityID])
);
CREATE UNIQUE INDEX [AK_SalesPersonQuotaHistory_rowguid]
    ON [Sales].[SalesPersonQuotaHistory] ([rowguid]);

-- ======================================================================
-- [Sales].[SalesReason]
-- ======================================================================
CREATE TABLE [Sales].[SalesReason] (
    [SalesReasonID] INT NOT NULL,
    [Name] NVARCHAR(50) NOT NULL,
    [ReasonType] NVARCHAR(50) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_SalesReason] PRIMARY KEY ([SalesReasonID])
);

-- ======================================================================
-- [Sales].[SalesTaxRate]
-- ======================================================================
CREATE TABLE [Sales].[SalesTaxRate] (
    [SalesTaxRateID] INT NOT NULL,
    [StateProvinceID] INT NOT NULL,
    [TaxType] TINYINT NOT NULL,
    [TaxRate] SMALLMONEY DEFAULT ((0.00)) NOT NULL,
    [Name] NVARCHAR(50) NOT NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_SalesTaxRate] PRIMARY KEY ([SalesTaxRateID]),
    CONSTRAINT [FK_SalesTaxRate_StateProvince_StateProvinceID] FOREIGN KEY ([StateProvinceID])
        REFERENCES [Person].[StateProvince] ([StateProvinceID])
);
CREATE UNIQUE INDEX [AK_SalesTaxRate_rowguid]
    ON [Sales].[SalesTaxRate] ([rowguid]);
CREATE UNIQUE INDEX [AK_SalesTaxRate_StateProvinceID_TaxType]
    ON [Sales].[SalesTaxRate] ([StateProvinceID], [TaxType]);

-- ======================================================================
-- [Sales].[SalesTerritory]
-- ======================================================================
CREATE TABLE [Sales].[SalesTerritory] (
    [TerritoryID] INT NOT NULL,
    [Name] NVARCHAR(50) NOT NULL,
    [CountryRegionCode] NVARCHAR(3) NOT NULL,
    [Group] NVARCHAR(50) NOT NULL,
    [SalesYTD] MONEY DEFAULT ((0.00)) NOT NULL,
    [SalesLastYear] MONEY DEFAULT ((0.00)) NOT NULL,
    [CostYTD] MONEY DEFAULT ((0.00)) NOT NULL,
    [CostLastYear] MONEY DEFAULT ((0.00)) NOT NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_SalesTerritory] PRIMARY KEY ([TerritoryID]),
    CONSTRAINT [FK_SalesTerritory_CountryRegion_CountryRegionCode] FOREIGN KEY ([CountryRegionCode])
        REFERENCES [Person].[CountryRegion] ([CountryRegionCode])
);
CREATE UNIQUE INDEX [AK_SalesTerritory_Name]
    ON [Sales].[SalesTerritory] ([Name]);
CREATE UNIQUE INDEX [AK_SalesTerritory_rowguid]
    ON [Sales].[SalesTerritory] ([rowguid]);

-- ======================================================================
-- [Sales].[SalesTerritoryHistory]
-- ======================================================================
CREATE TABLE [Sales].[SalesTerritoryHistory] (
    [BusinessEntityID] INT NOT NULL,
    [TerritoryID] INT NOT NULL,
    [StartDate] DATETIME NOT NULL,
    [EndDate] DATETIME NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_SalesTerritoryHistory] PRIMARY KEY ([BusinessEntityID], [StartDate], [TerritoryID]),
    CONSTRAINT [FK_SalesTerritoryHistory_SalesPerson_BusinessEntityID] FOREIGN KEY ([BusinessEntityID])
        REFERENCES [Sales].[SalesPerson] ([BusinessEntityID]),
    CONSTRAINT [FK_SalesTerritoryHistory_SalesTerritory_TerritoryID] FOREIGN KEY ([TerritoryID])
        REFERENCES [Sales].[SalesTerritory] ([TerritoryID])
);
CREATE UNIQUE INDEX [AK_SalesTerritoryHistory_rowguid]
    ON [Sales].[SalesTerritoryHistory] ([rowguid]);

-- ======================================================================
-- [Sales].[ShoppingCartItem]
-- ======================================================================
CREATE TABLE [Sales].[ShoppingCartItem] (
    [ShoppingCartItemID] INT NOT NULL,
    [ShoppingCartID] NVARCHAR(50) NOT NULL,
    [Quantity] INT DEFAULT ((1)) NOT NULL,
    [ProductID] INT NOT NULL,
    [DateCreated] DATETIME DEFAULT (getdate()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_ShoppingCartItem] PRIMARY KEY ([ShoppingCartItemID]),
    CONSTRAINT [FK_ShoppingCartItem_Product_ProductID] FOREIGN KEY ([ProductID])
        REFERENCES [Production].[Product] ([ProductID])
);
CREATE INDEX [IX_ShoppingCartItem_ShoppingCartID_ProductID]
    ON [Sales].[ShoppingCartItem] ([ShoppingCartID], [ProductID]);

-- ======================================================================
-- [Sales].[SpecialOffer]
-- ======================================================================
CREATE TABLE [Sales].[SpecialOffer] (
    [SpecialOfferID] INT NOT NULL,
    [Description] NVARCHAR(255) NOT NULL,
    [DiscountPct] SMALLMONEY DEFAULT ((0.00)) NOT NULL,
    [Type] NVARCHAR(50) NOT NULL,
    [Category] NVARCHAR(50) NOT NULL,
    [StartDate] DATETIME NOT NULL,
    [EndDate] DATETIME NOT NULL,
    [MinQty] INT DEFAULT ((0)) NOT NULL,
    [MaxQty] INT NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_SpecialOffer] PRIMARY KEY ([SpecialOfferID])
);
CREATE UNIQUE INDEX [AK_SpecialOffer_rowguid]
    ON [Sales].[SpecialOffer] ([rowguid]);

-- ======================================================================
-- [Sales].[SpecialOfferProduct]
-- ======================================================================
CREATE TABLE [Sales].[SpecialOfferProduct] (
    [SpecialOfferID] INT NOT NULL,
    [ProductID] INT NOT NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_SpecialOfferProduct] PRIMARY KEY ([SpecialOfferID], [ProductID]),
    CONSTRAINT [FK_SpecialOfferProduct_Product_ProductID] FOREIGN KEY ([ProductID])
        REFERENCES [Production].[Product] ([ProductID]),
    CONSTRAINT [FK_SpecialOfferProduct_SpecialOffer_SpecialOfferID] FOREIGN KEY ([SpecialOfferID])
        REFERENCES [Sales].[SpecialOffer] ([SpecialOfferID])
);
CREATE UNIQUE INDEX [AK_SpecialOfferProduct_rowguid]
    ON [Sales].[SpecialOfferProduct] ([rowguid]);
CREATE INDEX [IX_SpecialOfferProduct_ProductID]
    ON [Sales].[SpecialOfferProduct] ([ProductID]);

-- ======================================================================
-- [Sales].[Store]
-- ======================================================================
CREATE TABLE [Sales].[Store] (
    [BusinessEntityID] INT NOT NULL,
    [Name] NVARCHAR(50) NOT NULL,
    [SalesPersonID] INT NULL,
    [Demographics] XML NULL,
    [rowguid] UNIQUEIDENTIFIER DEFAULT (newid()) NOT NULL,
    [ModifiedDate] DATETIME DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [PK_Store] PRIMARY KEY ([BusinessEntityID]),
    CONSTRAINT [FK_Store_BusinessEntity_BusinessEntityID] FOREIGN KEY ([BusinessEntityID])
        REFERENCES [Person].[BusinessEntity] ([BusinessEntityID]),
    CONSTRAINT [FK_Store_SalesPerson_SalesPersonID] FOREIGN KEY ([SalesPersonID])
        REFERENCES [Sales].[SalesPerson] ([BusinessEntityID])
);
CREATE UNIQUE INDEX [AK_Store_rowguid]
    ON [Sales].[Store] ([rowguid]);
CREATE INDEX [IX_Store_SalesPersonID]
    ON [Sales].[Store] ([SalesPersonID]);
CREATE INDEX [PXML_Store_Demographics]
    ON [Sales].[Store] ([Demographics]);
