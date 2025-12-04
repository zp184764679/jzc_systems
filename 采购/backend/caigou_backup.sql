-- MySQL dump 10.13  Distrib 9.0.1, for Win64 (x86_64)
--
-- Host: localhost    Database: caigou
-- ------------------------------------------------------
-- Server version	9.0.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `invoices`
--

DROP TABLE IF EXISTS `invoices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `invoices` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `supplier_id` bigint unsigned NOT NULL,
  `po_id` bigint unsigned NOT NULL,
  `quote_id` bigint unsigned DEFAULT NULL,
  `invoice_code` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `invoice_number` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `invoice_date` datetime DEFAULT NULL,
  `buyer_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `buyer_tax_id` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `seller_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `seller_tax_id` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `amount_before_tax` decimal(12,2) DEFAULT NULL,
  `tax_amount` decimal(12,2) DEFAULT NULL,
  `total_amount` decimal(12,2) DEFAULT NULL,
  `amount` decimal(12,2) NOT NULL,
  `currency` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `file_url` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `file_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `file_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `file_size` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `remark` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `approval_notes` text COLLATE utf8mb4_unicode_ci,
  `approved_by` bigint unsigned DEFAULT NULL,
  `approved_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `uploaded_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `expiry_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `invoice_number` (`invoice_number`),
  KEY `idx_invoices_quote_id` (`quote_id`),
  KEY `idx_invoices_created_at` (`created_at`),
  KEY `idx_invoices_supplier_id` (`supplier_id`),
  KEY `idx_invoices_po_id` (`po_id`),
  KEY `idx_invoices_status` (`status`),
  KEY `idx_invoices_number` (`invoice_number`),
  KEY `idx_invoices_date` (`invoice_date`),
  KEY `idx_invoices_expiry` (`expiry_date`),
  KEY `idx_invoices_status_expiry` (`status`,`expiry_date`),
  CONSTRAINT `invoices_ibfk_1` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`) ON DELETE CASCADE,
  CONSTRAINT `invoices_ibfk_2` FOREIGN KEY (`po_id`) REFERENCES `purchase_orders` (`id`) ON DELETE CASCADE,
  CONSTRAINT `invoices_ibfk_3` FOREIGN KEY (`quote_id`) REFERENCES `supplier_quotes` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `invoices`
--

LOCK TABLES `invoices` WRITE;
/*!40000 ALTER TABLE `invoices` DISABLE KEYS */;
INSERT INTO `invoices` VALUES (1,2,2,5,NULL,'25442000000566464589','2025-09-16 00:00:00',NULL,NULL,NULL,NULL,NULL,NULL,NULL,16800.00,'CNY','/uploads/1f38461b4cec4c6080b6e7d4224c6336.pdf','粤B809SA专票.pdf','application/pdf','82.18KB','',NULL,'approved','批准',1,'2025-11-08 06:56:53','2025-11-08 06:56:41','2025-11-08 06:56:41','2025-11-08 06:56:53',NULL);
/*!40000 ALTER TABLE `invoices` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notifications`
--

DROP TABLE IF EXISTS `notifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notifications` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `recipient_id` bigint unsigned NOT NULL,
  `recipient_type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `notification_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `message` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `related_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `related_id` bigint unsigned DEFAULT NULL,
  `data` text COLLATE utf8mb4_unicode_ci,
  `is_read` tinyint(1) NOT NULL,
  `read_at` datetime DEFAULT NULL,
  `is_sent` tinyint(1) NOT NULL,
  `sent_at` datetime DEFAULT NULL,
  `send_method` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_notifications_type` (`notification_type`),
  KEY `idx_notifications_read` (`is_read`),
  KEY `idx_notifications_created_at` (`created_at`),
  KEY `idx_notifications_recipient_id` (`recipient_id`),
  KEY `idx_notifications_is_read` (`is_read`),
  KEY `idx_notifications_recipient_type` (`recipient_type`),
  KEY `idx_notif_recipient_read` (`recipient_id`,`is_read`,`created_at` DESC)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notifications`
--

LOCK TABLES `notifications` WRITE;
/*!40000 ALTER TABLE `notifications` DISABLE KEYS */;
INSERT INTO `notifications` VALUES (1,1,'user','pr_approved','【审批通过】251107001','您的采购申请已审批通过：\n\n📋 申请单号：251107001\n✅ 审批状态：已通过\n📅 审批时间：2025-11-08 01:53\n\n系统将自动创建询价单。','pr',1,NULL,0,NULL,1,'2025-11-07 17:53:23','in_app','2025-11-07 17:53:23'),(2,1,'user','pr_approved','【审批通过】251107001','您的采购申请已审批通过：\n\n📋 申请单号：251107001\n✅ 审批状态：已通过\n📅 审批时间：2025-11-08 01:54\n\n系统将自动创建询价单。','pr',1,NULL,0,NULL,1,'2025-11-07 17:54:55','in_app','2025-11-07 17:54:55'),(3,1,'user','pr_approved','【审批通过】251107001','您的采购申请已审批通过：\n\n📋 申请单号：251107001\n✅ 审批状态：已通过\n📅 审批时间：2025-11-08 01:56\n\n系统将自动创建询价单。','pr',1,NULL,0,NULL,1,'2025-11-07 17:56:58','in_app','2025-11-07 17:56:58'),(4,1,'user','pr_approved','【审批通过】251107001','您的采购申请已审批通过：\n\n📋 申请单号：251107001\n✅ 审批状态：已通过\n📅 审批时间：2025-11-08 02:00\n\n系统将自动创建询价单。','pr',1,NULL,0,NULL,1,'2025-11-07 18:00:53','in_app','2025-11-07 18:00:53'),(5,1,'user','pr_approved','【审批通过】251107001','您的采购申请已审批通过：\n\n📋 申请单号：251107001\n✅ 审批状态：已通过\n📅 审批时间：2025-11-08 02:02\n\n系统将自动创建询价单。','pr',1,NULL,0,NULL,1,'2025-11-07 18:02:30','in_app','2025-11-07 18:02:30'),(6,1,'user','pr_approved','【审批通过】251107001','您的采购申请已审批通过：\n\n📋 申请单号：251107001\n✅ 审批状态：已通过\n📅 审批时间：2025-11-08 02:09\n\n系统将自动创建询价单。','pr',1,NULL,0,NULL,1,'2025-11-07 18:09:07','in_app','2025-11-07 18:09:07'),(7,1,'user','pr_approved','【审批通过】251107001','您的采购申请已审批通过：\n\n📋 申请单号：251107001\n✅ 审批状态：已通过\n📅 审批时间：2025-11-08 02:09\n\n系统将自动创建询价单。','pr',1,NULL,0,NULL,1,'2025-11-07 18:09:56','in_app','2025-11-07 18:09:56'),(8,1,'user','pr_approved','【审批通过】251107001','您的采购申请已审批通过：\n\n📋 申请单号：251107001\n✅ 审批状态：已通过\n📅 审批时间：2025-11-08 02:12\n\n系统将自动创建询价单。','pr',1,NULL,0,NULL,1,'2025-11-07 18:12:40','in_app','2025-11-07 18:12:40'),(9,1,'user','pr_approved','【审批通过】251107001','您的采购申请已审批通过：\n\n📋 申请单号：251107001\n✅ 审批状态：已通过\n📅 审批时间：2025-11-08 02:14\n\n系统将自动创建询价单。','pr',1,NULL,0,NULL,1,'2025-11-07 18:14:24','in_app','2025-11-07 18:14:24'),(10,1,'user','pr_approved','【审批通过】251107001','您的采购申请已审批通过：\n\n📋 申请单号：251107001\n✅ 审批状态：已通过\n📅 审批时间：2025-11-08 02:16\n\n系统将自动创建询价单。','pr',1,NULL,0,NULL,1,'2025-11-07 18:16:48','in_app','2025-11-07 18:16:48'),(11,1,'user','pr_approved','【审批通过】251107001','您的采购申请已审批通过：\n\n📋 申请单号：251107001\n✅ 审批状态：已通过\n📅 审批时间：2025-11-08 02:17\n\n系统将自动创建询价单。','pr',1,NULL,0,NULL,1,'2025-11-07 18:17:48','in_app','2025-11-07 18:17:48'),(12,1,'user','pr_approved','【审批通过】251107001','您的采购申请已审批通过：\n\n📋 申请单号：251107001\n✅ 审批状态：已通过\n📅 审批时间：2025-11-08 02:20\n\n系统将自动创建询价单。','pr',1,NULL,0,NULL,1,'2025-11-07 18:20:08','in_app','2025-11-07 18:20:08'),(13,1,'user','pr_approved','【审批通过】251107001','您的采购申请已审批通过：\n\n📋 申请单号：251107001\n✅ 审批状态：已通过\n📅 审批时间：2025-11-08 02:21\n\n系统将自动创建询价单。','pr',1,NULL,0,NULL,1,'2025-11-07 18:21:10','in_app','2025-11-07 18:21:10'),(14,1,'user','pr_approved','【审批通过】251107001','您的采购申请已审批通过：\n\n📋 申请单号：251107001\n✅ 审批状态：已通过\n📅 审批时间：2025-11-08 02:22\n\n系统将自动创建询价单。','pr',1,NULL,0,NULL,1,'2025-11-07 18:22:18','in_app','2025-11-07 18:22:18'),(15,1,'user','pr_approved','【审批通过】251107001','您的采购申请已审批通过：\n\n📋 申请单号：251107001\n✅ 审批状态：已通过\n📅 审批时间：2025-11-08 02:26\n\n系统将自动创建询价单。','pr',1,NULL,0,NULL,1,'2025-11-07 18:26:29','in_app','2025-11-07 18:26:29'),(16,1,'user','pr_approved','【审批通过】251107001','您的采购申请已审批通过：\n\n📋 申请单号：251107001\n✅ 审批状态：已通过\n📅 审批时间：2025-11-08 02:27\n\n系统将自动创建询价单。','pr',1,NULL,0,NULL,1,'2025-11-07 18:27:37','in_app','2025-11-07 18:27:37'),(17,1,'user','pr_approved','【审批通过】251107001','您的采购申请已审批通过：\n\n📋 申请单号：251107001\n✅ 审批状态：已通过\n📅 审批时间：2025-11-08 02:36\n\n系统将自动创建询价单。','pr',1,NULL,0,NULL,1,'2025-11-07 18:36:28','in_app','2025-11-07 18:36:28'),(18,1,'user','pr_approved','【审批通过】251107001','您的采购申请已审批通过：\n\n📋 申请单号：251107001\n✅ 审批状态：已通过\n📅 审批时间：2025-11-08 02:37\n\n系统将自动创建询价单。','pr',1,NULL,0,NULL,1,'2025-11-07 18:37:16','in_app','2025-11-07 18:37:16'),(19,1,'user','pr_approved','【审批通过】251107001','您的采购申请已审批通过：\n\n📋 申请单号：251107001\n✅ 审批状态：已通过\n📅 审批时间：2025-11-08 02:38\n\n系统将自动创建询价单。','pr',1,NULL,0,NULL,1,'2025-11-07 18:38:15','in_app','2025-11-07 18:38:15'),(20,1,'user','pr_approved','【审批通过】251107001','您的采购申请已审批通过：\n\n📋 申请单号：251107001\n✅ 审批状态：已通过\n📅 审批时间：2025-11-08 02:40\n\n系统将自动创建询价单。','pr',1,NULL,0,NULL,1,'2025-11-07 18:40:04','in_app','2025-11-07 18:40:04'),(21,1,'user','pr_approved','【审批通过】251107001','您的采购申请已审批通过：\n\n📋 申请单号：251107001\n✅ 审批状态：已通过\n📅 审批时间：2025-11-08 02:41\n\n系统将自动创建询价单。','pr',1,NULL,0,NULL,1,'2025-11-07 18:41:22','in_app','2025-11-07 18:41:22'),(22,1,'user','pr_approved','【审批通过】251107002','您的采购申请已审批通过：\n\n📋 申请单号：251107002\n✅ 审批状态：已通过\n📅 审批时间：2025-11-08 03:18\n\n系统将自动创建询价单。','pr',2,NULL,0,NULL,1,'2025-11-07 19:18:09','in_app','2025-11-07 19:18:09'),(23,1,'user','pr_approved','【审批通过】251108001','您的采购申请已审批通过：\n\n📋 申请单号：251108001\n✅ 审批状态：已通过\n📅 审批时间：2025-11-08 11:06\n\n系统将自动创建询价单。','pr',3,NULL,0,NULL,1,'2025-11-08 03:06:31','in_app','2025-11-08 03:06:31'),(24,2,'supplier','po_created','新采购订单 PO-20251108-00001','您好 132321321，\n\n您有一个新的采购订单待处理：\n\n📋 订单号：PO-20251108-00001\n💰 订单金额：¥333.00\n🚚 交货期：7 天\n📅 发票截止日期：2025-11-15\n\n⚠️ 请在 7 天内上传发票，逾期将影响后续合作。\n\n请登录系统查看详情并上传发票。\n','purchase_order',1,'{\"po_id\": 1, \"po_number\": \"PO-20251108-00001\", \"total_price\": 333.0, \"lead_time\": 7, \"invoice_due_date\": \"2025-11-15T03:18:09\", \"days_remaining\": 7}',0,NULL,1,'2025-11-08 03:18:09','in_app','2025-11-08 03:18:09'),(25,2,'supplier','po_created','新采购订单 PO-20251108-00002','您好 132321321，\n\n您有一个新的采购订单待处理：\n\n📋 订单号：PO-20251108-00002\n💰 订单金额：¥3,232.00\n🚚 交货期：7 天\n📅 发票截止日期：2025-11-15\n\n⚠️ 请在 6 天内上传发票，逾期将影响后续合作。\n\n请登录系统查看详情并上传发票。\n','purchase_order',2,'{\"po_id\": 2, \"po_number\": \"PO-20251108-00002\", \"total_price\": 3232.0, \"lead_time\": 7, \"invoice_due_date\": \"2025-11-15T03:45:59\", \"days_remaining\": 6}',0,NULL,1,'2025-11-08 03:45:59','in_app','2025-11-08 03:45:59'),(26,2,'supplier','invoice_approved','发票 25442000000566464589 已批准','您好 132321321，\n\n您提交的发票已审批通过：\n\n📄 发票号：25442000000566464589\n💰 发票金额：¥16,800.00\n📋 关联订单：PO-20251108-00002\n✅ 审批状态：已批准\n⏰ 审批时间：2025-11-08 06:56\n\n财务将按照合同约定的付款条件进行付款处理。\n','invoice',1,'{\"invoice_id\": 1, \"invoice_number\": \"25442000000566464589\", \"amount\": 16800.0, \"po_number\": \"PO-20251108-00002\", \"approved_at\": \"2025-11-08T06:56:53\"}',0,NULL,1,'2025-11-08 06:56:53','in_app','2025-11-08 06:56:53');
/*!40000 ALTER TABLE `notifications` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pr`
--

DROP TABLE IF EXISTS `pr`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pr` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `pr_number` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `urgency` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `owner_id` bigint unsigned NOT NULL,
  `status` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_pr_pr_number` (`pr_number`),
  KEY `idx_pr_status` (`status`),
  KEY `idx_pr_owner_id` (`owner_id`),
  KEY `idx_pr_created_at` (`created_at`),
  KEY `idx_pr_status_created` (`status`,`created_at` DESC),
  KEY `idx_pr_owner_status` (`owner_id`,`status`),
  CONSTRAINT `pr_ibfk_1` FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pr`
--

LOCK TABLES `pr` WRITE;
/*!40000 ALTER TABLE `pr` DISABLE KEYS */;
INSERT INTO `pr` VALUES (1,'251107001','刀具采购','需求到货日: 2025-11-07 | 收货地: 11 | 物流备注: 11','medium',NULL,'2025-11-07 17:42:01',1,'cancelled'),(2,'251107002','11221','需求到货日: 2025-11-07 | 收货地: 深圳 | 物流备注: 是 ','medium',NULL,'2025-11-07 19:17:59',1,'approved'),(3,'251108001','刀具采购','需求到货日: 2025-11-08 | 收货地: 深圳 | 物流备注: 111','medium',NULL,'2025-11-08 03:06:18',1,'approved');
/*!40000 ALTER TABLE `pr` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pr_counters`
--

DROP TABLE IF EXISTS `pr_counters`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pr_counters` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `date_key` varchar(8) COLLATE utf8mb4_unicode_ci NOT NULL,
  `seq` bigint unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_pr_counters_date_key` (`date_key`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pr_counters`
--

LOCK TABLES `pr_counters` WRITE;
/*!40000 ALTER TABLE `pr_counters` DISABLE KEYS */;
INSERT INTO `pr_counters` VALUES (1,'20251107',2),(2,'20251108',1);
/*!40000 ALTER TABLE `pr_counters` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pr_item`
--

DROP TABLE IF EXISTS `pr_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pr_item` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `pr_id` bigint unsigned NOT NULL,
  `name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `spec` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `qty` int NOT NULL,
  `unit` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `remark` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `classification` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_pr_item_pr_id` (`pr_id`),
  KEY `idx_pr_item_classification` (`classification`),
  KEY `idx_pr_item_status` (`status`),
  CONSTRAINT `pr_item_ibfk_1` FOREIGN KEY (`pr_id`) REFERENCES `pr` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pr_item`
--

LOCK TABLES `pr_item` WRITE;
/*!40000 ALTER TABLE `pr_item` DISABLE KEYS */;
INSERT INTO `pr_item` VALUES (1,1,'镗刀','11',1,'件','1','cancelled',NULL),(2,1,'镗刀','11',1,'件','1','cancelled',NULL),(3,1,'镗刀','11',1,'件','1','cancelled',NULL),(4,2,'镗刀','11',1,'件','11','approved',NULL),(5,2,'镗刀','11',1,'件','11','approved',NULL),(6,2,'镗刀','11',1,'件','11','approved',NULL),(7,3,'镗刀','1',1,'件','1','approved',NULL),(8,3,'镗刀','1',1,'件','1','approved',NULL),(9,3,'镗刀','1',1,'件','1','approved',NULL);
/*!40000 ALTER TABLE `pr_item` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `purchase_orders`
--

DROP TABLE IF EXISTS `purchase_orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `purchase_orders` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `po_number` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `rfq_id` bigint unsigned NOT NULL,
  `quote_id` bigint unsigned NOT NULL,
  `supplier_id` bigint unsigned NOT NULL,
  `supplier_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `total_price` decimal(12,2) NOT NULL,
  `lead_time` int DEFAULT NULL,
  `quote_data` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `invoice_due_date` datetime DEFAULT NULL,
  `invoice_uploaded` tinyint(1) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `confirmed_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_purchase_orders_po_number` (`po_number`),
  KEY `idx_po_supplier_id` (`supplier_id`),
  KEY `idx_po_rfq_id` (`rfq_id`),
  KEY `idx_po_created_at` (`created_at`),
  KEY `idx_po_quote_id` (`quote_id`),
  KEY `idx_po_status` (`status`),
  KEY `idx_po_supplier_status` (`supplier_id`,`status`),
  KEY `idx_po_invoice_due` (`invoice_due_date`),
  CONSTRAINT `purchase_orders_ibfk_1` FOREIGN KEY (`rfq_id`) REFERENCES `rfqs` (`id`),
  CONSTRAINT `purchase_orders_ibfk_2` FOREIGN KEY (`quote_id`) REFERENCES `supplier_quotes` (`id`),
  CONSTRAINT `purchase_orders_ibfk_3` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `purchase_orders`
--

LOCK TABLES `purchase_orders` WRITE;
/*!40000 ALTER TABLE `purchase_orders` DISABLE KEYS */;
INSERT INTO `purchase_orders` VALUES (1,'PO-20251108-00001',27,3,2,'132321321',333.00,7,'{\"items\": [{\"item_name\": \"\\u9557\\u5200\", \"item_description\": \"1\", \"quantity_requested\": 1, \"unit\": \"\\u4ef6\", \"unit_price\": 333, \"subtotal\": 333}], \"notes\": \"\"}','confirmed','2025-11-15 03:18:09',0,'2025-11-08 03:18:09','2025-11-08 03:18:09','2025-11-08 03:18:09'),(2,'PO-20251108-00002',29,5,2,'132321321',3232.00,7,'{\"items\": [{\"item_name\": \"\\u9557\\u5200\", \"item_description\": \"11\", \"quantity_requested\": 1, \"unit\": \"\\u4ef6\", \"unit_price\": 3232, \"subtotal\": 3232}], \"notes\": \"\"}','confirmed','2025-11-15 03:45:59',1,'2025-11-08 03:45:59','2025-11-08 03:45:59','2025-11-08 06:56:41');
/*!40000 ALTER TABLE `purchase_orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `receipts`
--

DROP TABLE IF EXISTS `receipts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `receipts` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `po_id` bigint unsigned NOT NULL,
  `receiver_id` bigint unsigned DEFAULT NULL,
  `receipt_number` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `received_date` datetime NOT NULL,
  `quality_status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `quantity_received` int DEFAULT NULL,
  `notes` text COLLATE utf8mb4_unicode_ci,
  `photos` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `created_by` bigint unsigned DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `receipt_number` (`receipt_number`),
  KEY `created_by` (`created_by`),
  KEY `idx_receipts_receiver_id` (`receiver_id`),
  KEY `idx_receipts_po_id` (`po_id`),
  KEY `idx_receipts_received_date` (`received_date`),
  KEY `idx_receipts_status` (`status`),
  CONSTRAINT `receipts_ibfk_1` FOREIGN KEY (`po_id`) REFERENCES `purchase_orders` (`id`) ON DELETE CASCADE,
  CONSTRAINT `receipts_ibfk_2` FOREIGN KEY (`receiver_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
  CONSTRAINT `receipts_ibfk_3` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `receipts`
--

LOCK TABLES `receipts` WRITE;
/*!40000 ALTER TABLE `receipts` DISABLE KEYS */;
/*!40000 ALTER TABLE `receipts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rfq_items`
--

DROP TABLE IF EXISTS `rfq_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rfq_items` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `rfq_id` bigint unsigned NOT NULL,
  `pr_item_id` bigint unsigned NOT NULL,
  `item_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `item_spec` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `quantity` int NOT NULL,
  `unit` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `category` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `major_category` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `minor_category` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `classification_source` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `classification_score` longtext COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `idx_rfq_items_category` (`category`),
  KEY `idx_rfq_items_major_category` (`major_category`),
  KEY `idx_rfq_items_rfq_id` (`rfq_id`),
  KEY `idx_rfq_items_pr_item_id` (`pr_item_id`),
  KEY `idx_rfq_items_major_cat` (`major_category`),
  KEY `idx_rfq_items_rfq_category` (`rfq_id`,`category`),
  CONSTRAINT `rfq_items_ibfk_1` FOREIGN KEY (`rfq_id`) REFERENCES `rfqs` (`id`),
  CONSTRAINT `rfq_items_ibfk_2` FOREIGN KEY (`pr_item_id`) REFERENCES `pr_item` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=72 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rfq_items`
--

LOCK TABLES `rfq_items` WRITE;
/*!40000 ALTER TABLE `rfq_items` DISABLE KEYS */;
INSERT INTO `rfq_items` VALUES (51,23,4,'镗刀','11',1,'件','刀具/丝锥铰刀镗刀','刀具','丝锥铰刀镗刀','rule','{\"刀具/丝锥铰刀镗刀\": 1.0}'),(52,23,5,'镗刀','11',1,'件','刀具/丝锥铰刀镗刀','刀具','丝锥铰刀镗刀','rule','{\"刀具/丝锥铰刀镗刀\": 1.0}'),(53,23,6,'镗刀','11',1,'件','刀具/丝锥铰刀镗刀','刀具','丝锥铰刀镗刀','rule','{\"刀具/丝锥铰刀镗刀\": 1.0}'),(54,24,4,'镗刀','11',1,'件','刀具/丝锥铰刀镗刀','刀具','','manual','{}'),(55,24,5,'镗刀','11',1,'件','未分类','未分类','','manual','{}'),(56,24,6,'镗刀','11',1,'件','未分类','未分类','','manual','{}'),(57,25,7,'镗刀','1',1,'件','分类中...','','','pending','{}'),(58,25,8,'镗刀','1',1,'件','分类中...','','','pending','{}'),(59,25,9,'镗刀','1',1,'件','分类中...','','','pending','{}'),(60,26,7,'镗刀','1',1,'件','刀具/丝锥铰刀镗刀','刀具','','manual','{}'),(61,26,8,'镗刀','1',1,'件','未分类','未分类','','manual','{}'),(62,26,9,'镗刀','1',1,'件','未分类','未分类','','manual','{}'),(63,27,7,'镗刀','1',1,'件','刀具/丝锥铰刀镗刀','刀具','','manual','{}'),(64,27,8,'镗刀','1',1,'件','未分类','未分类','','manual','{}'),(65,27,9,'镗刀','1',1,'件','未分类','未分类','','manual','{}'),(66,28,4,'镗刀','11',1,'件','刀具/丝锥铰刀镗刀','刀具','','manual','{}'),(67,28,5,'镗刀','11',1,'件','未分类','未分类','','manual','{}'),(68,28,6,'镗刀','11',1,'件','未分类','未分类','','manual','{}'),(69,29,4,'镗刀','11',1,'件','刀具/丝锥铰刀镗刀','刀具','','manual','{}'),(70,29,5,'镗刀','11',1,'件','未分类','未分类','','manual','{}'),(71,29,6,'镗刀','11',1,'件','未分类','未分类','','manual','{}');
/*!40000 ALTER TABLE `rfq_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rfq_notification_tasks`
--

DROP TABLE IF EXISTS `rfq_notification_tasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rfq_notification_tasks` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `rfq_id` bigint unsigned NOT NULL,
  `supplier_id` bigint unsigned NOT NULL,
  `category` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `retry_count` bigint unsigned NOT NULL,
  `max_retries` bigint unsigned NOT NULL,
  `error_reason` text COLLATE utf8mb4_unicode_ci,
  `wecom_msg_id` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `sent_at` datetime DEFAULT NULL,
  `next_retry_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_rnt_supplier_id` (`supplier_id`),
  KEY `idx_rnt_rfq_id` (`rfq_id`),
  KEY `idx_rnt_status` (`status`),
  KEY `idx_rnt_next_retry_at` (`next_retry_at`),
  KEY `idx_rnt_status_retry` (`status`,`next_retry_at`),
  CONSTRAINT `rfq_notification_tasks_ibfk_1` FOREIGN KEY (`rfq_id`) REFERENCES `rfqs` (`id`),
  CONSTRAINT `rfq_notification_tasks_ibfk_2` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rfq_notification_tasks`
--

LOCK TABLES `rfq_notification_tasks` WRITE;
/*!40000 ALTER TABLE `rfq_notification_tasks` DISABLE KEYS */;
INSERT INTO `rfq_notification_tasks` VALUES (1,24,2,'刀具/丝锥铰刀镗刀','pending',0,5,NULL,NULL,'2025-11-07 19:32:04',NULL,NULL),(2,26,2,'刀具/丝锥铰刀镗刀','pending',0,5,NULL,NULL,'2025-11-08 03:06:52',NULL,NULL),(3,27,2,'刀具/丝锥铰刀镗刀','sent',0,5,NULL,NULL,'2025-11-08 03:16:00','2025-11-08 03:16:06',NULL),(4,28,2,'刀具/丝锥铰刀镗刀','pending',0,5,NULL,NULL,'2025-11-08 03:29:07',NULL,NULL),(5,29,2,'刀具/丝锥铰刀镗刀','sent',0,5,NULL,NULL,'2025-11-08 03:44:42','2025-11-08 03:44:44',NULL);
/*!40000 ALTER TABLE `rfq_notification_tasks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rfqs`
--

DROP TABLE IF EXISTS `rfqs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rfqs` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `pr_id` bigint unsigned NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `note` text COLLATE utf8mb4_unicode_ci,
  `payment_terms` int NOT NULL DEFAULT '90' COMMENT '付款周期(天)',
  `created_by` bigint unsigned DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `sent_at` datetime DEFAULT NULL,
  `closed_at` datetime DEFAULT NULL,
  `classification_status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '分类状态: pending/processing/completed/failed',
  `classification_task_id` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Celery任务ID',
  `classification_started_at` datetime DEFAULT NULL COMMENT '分类开始时间',
  `classification_completed_at` datetime DEFAULT NULL COMMENT '分类完成时间',
  PRIMARY KEY (`id`),
  KEY `idx_rfqs_pr_id` (`pr_id`),
  KEY `idx_rfqs_status` (`status`),
  KEY `idx_rfqs_created_at` (`created_at`),
  KEY `idx_rfq_pr_id` (`pr_id`),
  KEY `idx_rfq_status` (`status`),
  KEY `idx_rfq_created_at` (`created_at`),
  KEY `idx_rfq_created_by` (`created_by`),
  KEY `idx_rfq_status_created` (`status`,`created_at` DESC),
  KEY `idx_rfq_classification_status` (`classification_status`),
  CONSTRAINT `rfqs_ibfk_1` FOREIGN KEY (`pr_id`) REFERENCES `pr` (`id`),
  CONSTRAINT `rfqs_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rfqs`
--

LOCK TABLES `rfqs` WRITE;
/*!40000 ALTER TABLE `rfqs` DISABLE KEYS */;
INSERT INTO `rfqs` VALUES (23,2,'draft','自动从PR#2创建',90,1,'2025-11-07 19:18:09',NULL,NULL,NULL,NULL,NULL,NULL),(24,2,'sent','',90,1,'2025-11-07 19:32:04','2025-11-07 19:32:11',NULL,NULL,NULL,NULL,NULL),(25,3,'draft','自动从PR#3创建',90,1,'2025-11-08 03:06:31',NULL,NULL,'pending',NULL,NULL,NULL),(26,3,'sent','',90,1,'2025-11-08 03:06:52','2025-11-08 03:06:58',NULL,NULL,NULL,NULL,NULL),(27,3,'po_created','',90,1,'2025-11-08 03:16:00','2025-11-08 03:16:06',NULL,NULL,NULL,NULL,NULL),(28,2,'sent','',90,1,'2025-11-08 03:29:07','2025-11-08 03:29:09',NULL,NULL,NULL,NULL,NULL),(29,2,'po_created','',90,1,'2025-11-08 03:44:41','2025-11-08 03:44:44',NULL,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `rfqs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `supplier_categories`
--

DROP TABLE IF EXISTS `supplier_categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `supplier_categories` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `supplier_id` bigint unsigned NOT NULL,
  `category` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `major_category` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `minor_category` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_supplier_category` (`supplier_id`,`category`),
  KEY `idx_sc_supplier` (`supplier_id`),
  KEY `idx_sc_category` (`category`),
  KEY `ix_supplier_categories_major_category` (`major_category`),
  KEY `idx_sc_major` (`major_category`),
  KEY `idx_supplier_cat_supplier_id` (`supplier_id`),
  KEY `idx_supplier_cat_category` (`category`),
  KEY `idx_supplier_cat_major` (`major_category`),
  KEY `idx_sc_supplier_category` (`supplier_id`,`category`),
  CONSTRAINT `supplier_categories_ibfk_1` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `supplier_categories`
--

LOCK TABLES `supplier_categories` WRITE;
/*!40000 ALTER TABLE `supplier_categories` DISABLE KEYS */;
INSERT INTO `supplier_categories` VALUES (1,1,'General','General','','2025-11-07 18:56:46','2025-11-07 18:56:46'),(2,2,'刀具','刀具','','2025-11-07 19:18:41','2025-11-07 19:18:41');
/*!40000 ALTER TABLE `supplier_categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `supplier_quotes`
--

DROP TABLE IF EXISTS `supplier_quotes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `supplier_quotes` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `rfq_id` bigint unsigned NOT NULL,
  `rfq_item_id` bigint unsigned DEFAULT NULL COMMENT '关联的RFQ物料项ID，每个物料单独报价',
  `supplier_id` bigint unsigned NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `category` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '品类名称，如"刀具/铣削刀具"',
  `item_name` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `item_description` text COLLATE utf8mb4_unicode_ci,
  `quantity_requested` int DEFAULT NULL,
  `unit` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `total_price` decimal(12,2) DEFAULT NULL,
  `lead_time` int DEFAULT NULL,
  `supplier_name` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `payment_terms` int NOT NULL COMMENT '供应商报价付款周期(天)',
  `quote_number` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `quote_json` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime DEFAULT NULL,
  `responded_at` datetime DEFAULT NULL,
  `expired_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_supplier_quotes_quote_number` (`quote_number`),
  UNIQUE KEY `ix_supplier_quotes_supplier_rfq_item_id` (`supplier_id`,`rfq_id`,`rfq_item_id`),
  KEY `idx_sq_status` (`status`),
  KEY `idx_sq_supplier_id` (`supplier_id`),
  KEY `idx_sq_total_price` (`total_price`),
  KEY `ix_supplier_quotes_supplier_rfq_item` (`supplier_id`,`rfq_id`,`item_name`),
  KEY `ix_supplier_quotes_category` (`category`),
  KEY `idx_sq_rfq_id` (`rfq_id`),
  KEY `ix_supplier_quotes_status` (`status`),
  KEY `idx_supplier_quotes_rfq_id` (`rfq_id`),
  KEY `idx_supplier_quotes_supplier_id` (`supplier_id`),
  KEY `idx_supplier_quotes_status` (`status`),
  KEY `idx_supplier_quotes_category` (`category`),
  KEY `idx_sq_rfq_supplier` (`rfq_id`,`supplier_id`),
  KEY `idx_sq_supplier_status` (`supplier_id`,`status`),
  KEY `idx_sq_rfq_status` (`rfq_id`,`status`),
  KEY `idx_sq_rfq_item_id` (`rfq_item_id`),
  CONSTRAINT `fk_supplier_quotes_rfq_item` FOREIGN KEY (`rfq_item_id`) REFERENCES `rfq_items` (`id`) ON DELETE CASCADE,
  CONSTRAINT `supplier_quotes_ibfk_1` FOREIGN KEY (`rfq_id`) REFERENCES `rfqs` (`id`),
  CONSTRAINT `supplier_quotes_ibfk_2` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `supplier_quotes`
--

LOCK TABLES `supplier_quotes` WRITE;
/*!40000 ALTER TABLE `supplier_quotes` DISABLE KEYS */;
INSERT INTO `supplier_quotes` VALUES (1,24,NULL,2,'pending','刀具/丝锥铰刀镗刀',NULL,NULL,NULL,NULL,NULL,NULL,'132321321',90,NULL,'{\"items\": [{\"item_name\": \"镗刀\", \"item_description\": \"11\", \"quantity_requested\": 1, \"unit\": \"件\"}]}','2025-11-07 19:32:04',NULL,NULL),(2,26,NULL,2,'pending','刀具/丝锥铰刀镗刀',NULL,NULL,NULL,NULL,NULL,NULL,'132321321',90,NULL,'{\"items\": [{\"item_name\": \"镗刀\", \"item_description\": \"1\", \"quantity_requested\": 1, \"unit\": \"件\"}]}','2025-11-08 03:06:52',NULL,NULL),(3,27,NULL,2,'awarded','刀具/丝锥铰刀镗刀',NULL,NULL,NULL,NULL,333.00,7,'132321321',90,'251108-0002-003','{\"items\": [{\"item_name\": \"\\u9557\\u5200\", \"item_description\": \"1\", \"quantity_requested\": 1, \"unit\": \"\\u4ef6\", \"unit_price\": 333, \"subtotal\": 333}], \"notes\": \"\"}','2025-11-08 03:16:00','2025-11-08 03:17:38',NULL),(4,28,NULL,2,'pending','刀具/丝锥铰刀镗刀',NULL,NULL,NULL,NULL,NULL,NULL,'132321321',90,NULL,'{\"items\": [{\"item_name\": \"镗刀\", \"item_description\": \"11\", \"quantity_requested\": 1, \"unit\": \"件\"}]}','2025-11-08 03:29:07',NULL,NULL),(5,29,NULL,2,'awarded','刀具/丝锥铰刀镗刀',NULL,NULL,NULL,NULL,3232.00,7,'132321321',90,'251108-0002-005','{\"items\": [{\"item_name\": \"\\u9557\\u5200\", \"item_description\": \"11\", \"quantity_requested\": 1, \"unit\": \"\\u4ef6\", \"unit_price\": 3232, \"subtotal\": 3232}], \"notes\": \"\"}','2025-11-08 03:44:42','2025-11-08 03:45:42',NULL);
/*!40000 ALTER TABLE `supplier_quotes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `suppliers`
--

DROP TABLE IF EXISTS `suppliers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `suppliers` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `code` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `company_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tax_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `business_scope` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `credit_code` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tax_number` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `legal_representative` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `registered_capital` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `registered_address` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `established_date` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `company_type` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `business_status` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `province` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `city` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `district` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `address` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `contact_name` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `contact_phone` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `contact_email` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `company_phone` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `fax` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `website` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `office_address` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `postal_code` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `business_license_url` text COLLATE utf8mb4_unicode_ci,
  `license_file_type` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `license_file_size` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `company_description` text COLLATE utf8mb4_unicode_ci,
  `description` text COLLATE utf8mb4_unicode_ci,
  `main_products` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `annual_revenue` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `employee_count` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `factory_area` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `production_capacity` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `quality_certifications` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `bank_name` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `bank_account` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `bank_branch` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `swift_code` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `payment_terms` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `credit_rating` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tax_registration_number` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `invoice_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `rating` float DEFAULT NULL,
  `rating_updated_at` datetime DEFAULT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `reason` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `last_login_at` datetime DEFAULT NULL,
  `wechat_openid` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '微信服务号OpenID',
  `is_subscribed` tinyint(1) DEFAULT NULL COMMENT '是否关注公众号',
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `company_name` (`company_name`),
  UNIQUE KEY `code` (`code`),
  UNIQUE KEY `wechat_openid` (`wechat_openid`),
  KEY `idx_suppliers_status` (`status`),
  KEY `idx_suppliers_code` (`code`),
  KEY `idx_suppliers_email` (`contact_email`),
  KEY `idx_suppliers_company` (`company_name`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `suppliers`
--

LOCK TABLES `suppliers` WRITE;
/*!40000 ALTER TABLE `suppliers` DISABLE KEYS */;
INSERT INTO `suppliers` VALUES (1,NULL,'test_supplier_a@test.com','pbkdf2:sha256:600000$EraxU37iIojYJQfH$2f52d17fda2ac6e4d7febf2a3a79bec7aafcf2abc47bbe8993238effa0051804','测试供应商A','TEST123456','',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'','','','','张三','13800138001','',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'approved',NULL,'2025-11-07 18:56:46','2025-11-08 03:17:27',NULL,NULL,0),(2,NULL,'jzchardwar@gmail.com','pbkdf2:sha256:600000$YQztIjUNnOGYnMoa$8a31dc2d32a2188b7e2006fa68bb78b36ab8f391c44fc5981c69f6d4ffc90ef2','132321321','213321321','刀具',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'','','','','123132321','132321','jzchardwar@gmail.com',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,'approved',NULL,'2025-11-07 19:18:41','2025-11-08 04:38:16','2025-11-08 04:38:16',NULL,0);
/*!40000 ALTER TABLE `suppliers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `role` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `created_by` bigint unsigned DEFAULT NULL,
  `department` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `employee_no` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phone` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `wework_user_id` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `uq_users_employee_no` (`employee_no`),
  UNIQUE KEY `wework_user_id` (`wework_user_id`),
  KEY `idx_users_status` (`status`),
  KEY `idx_users_role` (`role`),
  KEY `idx_users_department` (`department`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'周鹏','jzchardware@gmail.com','pbkdf2:sha256:600000$EK6HROed75rkMBUz$f84fa0cfb92958751414e2d9badfe3a7337605f03fbcf91b0d5c6789481fc74d','approved','admin','2025-11-08 01:19:35',NULL,'',NULL,'13590217332',NULL),(2,'exzzz','exzzz@test.com','pbkdf2:sha256:600000$NMaq0RJjiEQG35PH$5b2f2eaf58d89b4a0fec64f10b55dbd8e00dc306310a00d1720ee4eb6e69e6bb','approved','user','2025-11-08 01:19:35',NULL,'',NULL,'13800000000',NULL);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-11-08 15:17:39
